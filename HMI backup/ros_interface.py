import math
import time

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

import config

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image, JointState
    from std_msgs.msg import String, Bool
    from geometry_msgs.msg import Twist, Point
    from rclpy.executors import MultiThreadedExecutor
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False

try:
    from physical_ai_interfaces.msg import TaskStatus, TrainingStatus, HFOperationStatus
    from physical_ai_interfaces.srv import SendCommand, GetSavedPolicyList
    PAI_AVAILABLE = True
except ImportError:
    PAI_AVAILABLE = False

_MOCK_JOINT_NAMES = [
    "shoulder_pan", "shoulder_lift", "elbow",
    "wrist_1", "wrist_2", "wrist_3",
]

STATE_LABELS = {
    "idle":       "IDLE",
    "warming_up": "OPWARMEN",
    "resetting":  "RESETTEN",
    "recording":  "OPNEMEN (LfD)",
    "saving":     "OPSLAAN",
    "stopped":    "GESTOPT",
    "autonomous": "AUTONOOM (INFERENCING)",
    "estop":      "NOODSTOP ACTIEF",
}


class RosWorker(QThread):
    image_received        = pyqtSignal(np.ndarray)
    joint_states_received = pyqtSignal(list, list)
    progress_received     = pyqtSignal(float)
    confidence_received   = pyqtSignal(float)
    grip_point_received   = pyqtSignal(float, float)
    state_changed         = pyqtSignal(str)
    log_message           = pyqtSignal(str)
    mode_changed          = pyqtSignal(str, str)
    collision_detected    = pyqtSignal(bool)
    policy_list_received  = pyqtSignal(list)   # lijst van policy paden

    def __init__(self):
        super().__init__()
        self.node = None
        self.active_mode = None
        self._cmd_pub = None
        self._twist_pub = None
        self._ros_initialized_here = False
        self._stop_requested = False
        self._task_client = None
        self._policy_client = None

        self._mock_state = "idle"
        self._mock_progress = 0.0
        self._frozen_positions = [0.0] * len(_MOCK_JOINT_NAMES)

    def run(self):
        self.active_mode = self._resolve_mode()
        if self.active_mode == "ros":
            self.mode_changed.emit("ros", "Verbonden met ROS2")
            self._run_ros()
        elif self.active_mode == "mock":
            reason = "rclpy niet gevonden" if not ROS_AVAILABLE else "demo-modus geforceerd via config.HMI_MODE"
            self.mode_changed.emit("mock", f"Demo-modus actief ({reason})")
            self._run_mock()
        else:
            self.mode_changed.emit(
                "error",
                "config.HMI_MODE='ros' maar rclpy is niet geïnstalleerd."
            )

    def _resolve_mode(self):
        if config.HMI_MODE == "mock":
            return "mock"
        if config.HMI_MODE == "ros":
            return "ros" if ROS_AVAILABLE else "error"
        return "ros" if ROS_AVAILABLE else "mock"

    # ── ROS BACKEND ────────────────────────────────────────────────────────────
    def _run_ros(self):
        if not rclpy.ok():
            rclpy.init()
            self._ros_initialized_here = True

        self.node = Node("pyqt_hmi_node")

        self.node.create_subscription(Image,      config.TOPIC_CAMERA_IMAGE, self._on_image, 10)
        self.node.create_subscription(JointState, config.TOPIC_JOINT_STATES, self._on_joint_states, 10)
        self.node.create_subscription(Bool,       config.TOPIC_COLLISION,    self._on_collision, 10)
        self.node.create_subscription(Point,      config.TOPIC_GRIP_POINT,   self._on_grip_point, 10)

        if PAI_AVAILABLE:
            self.node.create_subscription(TaskStatus,        config.TOPIC_TASK_STATUS, self._on_task_status, 10)
            self.node.create_subscription(TrainingStatus,    config.TOPIC_TRAINING,    self._on_training_status, 10)
            self.node.create_subscription(HFOperationStatus, config.TOPIC_HF_STATUS,   self._on_hf_status, 10)
            self._task_client   = self.node.create_client(SendCommand,       '/task/command')
            self._policy_client = self.node.create_client(GetSavedPolicyList, '/get_saved_policies')
            self.log_message.emit("physical_ai_interfaces gevonden — alle topics actief.")
        else:
            self.log_message.emit("WAARSCHUWING: physical_ai_interfaces niet gevonden.")

        self._cmd_pub   = self.node.create_publisher(String, config.TOPIC_COMMAND, 10)
        self._twist_pub = self.node.create_publisher(Twist,  config.TOPIC_CMD_VEL, 10)

        self.log_message.emit("ROS2-node gestart.")
        executor = MultiThreadedExecutor()
        executor.add_node(self.node)

        while not self._stop_requested:
            executor.spin_once(timeout_sec=0.1)

    def _on_image(self, msg):
        img = self._image_to_numpy(msg)
        if img is not None:
            self.image_received.emit(img)

    def _on_joint_states(self, msg):
        self.joint_states_received.emit(list(msg.name), list(msg.position))

    def _on_collision(self, msg):
        self.collision_detected.emit(bool(msg.data))
        if msg.data:
            self.log_message.emit("⚠️  COLLISION GEDETECTEERD!")

    def _on_task_status(self, msg):
        state = config.TASK_PHASE.get(msg.phase, "idle")
        self.state_changed.emit(state)
        if msg.current_task_instruction:
            self.log_message.emit(f"Instructie: {msg.current_task_instruction}")
        if msg.error:
            self.log_message.emit(f"FOUT: {msg.error}")
        if msg.total_storage_size > 0:
            self.log_message.emit(
                f"Opslag: {msg.used_storage_size:.1f}/{msg.total_storage_size:.1f} GB  |  "
                f"CPU: {msg.used_cpu:.0f}%  |  RAM: {msg.used_ram_size:.1f}/{msg.total_ram_size:.1f} GB"
            )
        if msg.total_time > 0:
            self.progress_received.emit((msg.proceed_time / msg.total_time) * 100)

    def _on_training_status(self, msg):
        if msg.is_training:
            if msg.training_info.steps > 0:
                self.progress_received.emit((msg.current_step / msg.training_info.steps) * 100)
            self.log_message.emit(
                f"Training: stap {msg.current_step}/{msg.training_info.steps}  |  loss: {msg.current_loss:.4f}"
            )
        if msg.error:
            self.log_message.emit(f"Training FOUT: {msg.error}")

    def _on_hf_status(self, msg):
        self.confidence_received.emit(msg.progress_percentage / 100.0)
        if msg.status not in ("", "Idle"):
            self.log_message.emit(
                f"HuggingFace {msg.operation}: {msg.status} — {msg.message} "
                f"({msg.progress_current}/{msg.progress_total})"
            )

    def _on_grip_point(self, msg):
        self.grip_point_received.emit(float(msg.x), float(msg.y))

    @staticmethod
    def _image_to_numpy(msg):
        try:
            arr = np.frombuffer(msg.data, dtype=np.uint8)
            if msg.encoding == "rgb8":
                return arr.reshape((msg.height, msg.width, 3)).copy()
            elif msg.encoding == "bgr8":
                img = arr.reshape((msg.height, msg.width, 3))
                return img[:, :, ::-1].copy()
            elif msg.encoding == "mono8":
                gray = arr.reshape((msg.height, msg.width))
                return np.stack([gray] * 3, axis=-1).copy()
            return None
        except Exception:
            return None

    # ── MODEL SELECTIE ─────────────────────────────────────────────────────────
    def get_policy_list(self):
        """Haal lijst van opgeslagen modellen op via service."""
        if self._policy_client is None:
            self.log_message.emit("Policy service niet beschikbaar.")
            return
        if not self._policy_client.wait_for_service(timeout_sec=2.0):
            self.log_message.emit("Policy service niet bereikbaar.")
            return
        future = self._policy_client.call_async(GetSavedPolicyList.Request())
        future.add_done_callback(self._on_policy_list)

    def _on_policy_list(self, future):
        try:
            result = future.result()
            if result.success:
                self.policy_list_received.emit(list(result.saved_policy_path))
                self.log_message.emit(f"{len(result.saved_policy_path)} modellen gevonden.")
            else:
                self.log_message.emit(f"Fout bij ophalen modellen: {result.message}")
        except Exception as e:
            self.log_message.emit(f"Policy service fout: {e}")

    def start_inference(self, policy_path: str):
        """Start inferencing met het opgegeven model."""
        if self._task_client is None:
            self.log_message.emit("Task service niet beschikbaar.")
            return
        if not self._task_client.wait_for_service(timeout_sec=2.0):
            self.log_message.emit("Task service niet bereikbaar.")
            return
        req = SendCommand.Request()
        req.command = 2                       # START_INFERENCE
        req.task_info.policy_path = policy_path
        future = self._task_client.call_async(req)
        future.add_done_callback(self._on_task_response)
        self.log_message.emit(f"Inferencing starten: {policy_path}")

    def stop_inference(self):
        """Stop de huidige taak."""
        if self._task_client is None:
            self.log_message.emit("Task service niet beschikbaar.")
            return
        if not self._task_client.wait_for_service(timeout_sec=2.0):
            self.log_message.emit("Task service niet bereikbaar.")
            return
        req = SendCommand.Request()
        req.command = 3                       # STOP
        future = self._task_client.call_async(req)
        future.add_done_callback(self._on_task_response)
        self.log_message.emit("Stop commando verzonden.")

    def _on_task_response(self, future):
        try:
            result = future.result()
            if result.success:
                self.log_message.emit(f"✓ {result.message}")
            else:
                self.log_message.emit(f"✗ {result.message}")
        except Exception as e:
            self.log_message.emit(f"Task service fout: {e}")

    # ── MOCK BACKEND ───────────────────────────────────────────────────────────
    def _run_mock(self):
        self.state_changed.emit(self._mock_state)
        self.log_message.emit("Robot niet gevonden. Demo-modus gestart!")
        t0 = time.time()
        while not self._stop_requested:
            t = time.time() - t0
            self._mock_tick(t)
            time.sleep(0.05)

    def _mock_tick(self, t):
        if self._mock_state != "estop":
            positions = [0.4 * math.sin(t * 0.5 + i) for i in range(len(_MOCK_JOINT_NAMES))]
            self._frozen_positions = positions
        else:
            positions = self._frozen_positions
        self.joint_states_received.emit(_MOCK_JOINT_NAMES, positions)

        confidence = 0.65 + 0.28 * math.sin(t * 0.8) if self._mock_state == "autonomous" else 0.0
        self.confidence_received.emit(max(0.0, min(1.0, confidence)))

        if self._mock_state == "training":
            self._mock_progress = min(100.0, self._mock_progress + 1.2)
            if self._mock_progress >= 100.0:
                self.log_message.emit("[DEMO] Training voltooid.")
                self._set_mock_state("idle")
        self.progress_received.emit(self._mock_progress)

        self.grip_point_received.emit(
            0.5 + 0.18 * math.sin(t * 0.6),
            0.5 + 0.12 * math.cos(t * 0.9)
        )
        self.image_received.emit(self._generate_mock_frame(t))

    @staticmethod
    def _generate_mock_frame(t):
        w, h = 480, 360
        yy, xx = np.indices((h, w))
        stripe = (xx + yy + int(t * 40)) % 60 < 30
        frame = np.empty((h, w, 3), dtype=np.uint8)
        frame[..., 0] = np.where(stripe, 40, 26)
        frame[..., 1] = np.where(stripe, 44, 30)
        frame[..., 2] = np.where(stripe, 50, 36)
        return frame

    def _set_mock_state(self, new_state):
        self._mock_state = new_state
        self.state_changed.emit(new_state)

    # ── COMMANDO'S ─────────────────────────────────────────────────────────────
    def send_command(self, text: str):
        self.log_message.emit(f"Commando verzonden: {text}")
        if self._cmd_pub is not None:
            msg = String()
            msg.data = text
            self._cmd_pub.publish(msg)
        if self.active_mode == "mock":
            self._handle_mock_command(text)

    def _handle_mock_command(self, text: str):
        if text == "start_recording":
            self._set_mock_state("recording")
        elif text == "stop_recording" and self._mock_state == "recording":
            self._set_mock_state("idle")
        elif text == "start_training":
            self._mock_progress = 0.0
            self._set_mock_state("training")
        elif text in ("start_robot", "test") and self._mock_state != "estop":
            self._set_mock_state("autonomous")
            self.log_message.emit("[DEMO] Robot gestart in autonome modus.")
        elif text == "stop_robot" and self._mock_state != "estop":
            self._set_mock_state("idle")
            self.log_message.emit("[DEMO] Robot gestopt.")
        elif text == "emergency_stop":
            self._set_mock_state("estop")
        elif text == "reset_estop" and self._mock_state == "estop":
            self._set_mock_state("idle")

    def send_jog(self, linear_x: float = 0.0, angular_z: float = 0.0):
        if self._twist_pub is not None:
            msg = Twist()
            msg.linear.x = linear_x
            msg.angular.z = angular_z
            self._twist_pub.publish(msg)

    def shutdown(self):
        self._stop_requested = True
        if self.node is not None:
            self.node.destroy_node()
        if self._ros_initialized_here and ROS_AVAILABLE:
            try:
                rclpy.shutdown()
            except Exception:
                pass
        self.quit()
        self.wait()
