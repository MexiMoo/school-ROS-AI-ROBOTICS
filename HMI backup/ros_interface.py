import math
import time

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal

import config

try:
    import rclpy
    from rclpy.node import Node
    from sensor_msgs.msg import Image, JointState
    from std_msgs.msg import String, Float32
    from geometry_msgs.msg import Twist, Point
    from rclpy.executors import MultiThreadedExecutor
    ROS_AVAILABLE = True
except ImportError:
    ROS_AVAILABLE = False


# DEMO joints. Fysieke joints komen van de /joint_states node.
_MOCK_JOINT_NAMES = [
    "shoulder_pan", "shoulder_lift", "elbow",
    "wrist_1", "wrist_2", "wrist_3",
]

# Statusen
STATE_LABELS = {
    "idle":       "IDLE",
    "recording":  "OPNEMEN (LfD)",
    "training":   "TRAINING",
    "autonomous": "AUTONOOM",
    "estop":      "NOODSTOP ACTIEF",
}


class RosWorker(QThread):
    image_received        = pyqtSignal(np.ndarray)    # RGB image (H, W, 3) uint8
    joint_states_received = pyqtSignal(list, list)    # joint-namen, posities (rad)
    progress_received     = pyqtSignal(float)         # 0-100
    confidence_received   = pyqtSignal(float)         # 0-1
    grip_point_received   = pyqtSignal(float, float)  # x, y genormaliseerd (0-1)
    state_changed         = pyqtSignal(str)           # idle/recording/training/autonomous/estop
    log_message           = pyqtSignal(str)           # vrije tekstregel voor het logboek
    mode_changed          = pyqtSignal(str, str)      # ("ros"|"mock"|"error", toelichting)

    def __init__(self):
        super().__init__()
        self.node = None
        self.active_mode = None
        self._cmd_pub = None
        self._twist_pub = None
        self._ros_initialized_here = False
        self._stop_requested = False

        # Status van mock state
        self._mock_state = "idle"
        self._mock_progress = 0.0
        self._frozen_positions = [0.0] * len(_MOCK_JOINT_NAMES)

    # Thread entrypoint
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
                "config.HMI_MODE='ros' maar rclpy is niet geïnstalleerd. "
                "Source je ROS2-setup.bash, of zet HMI_MODE op 'auto'/'mock'."
            )

    def _resolve_mode(self):
        if config.HMI_MODE == "mock":
            return "mock"
        if config.HMI_MODE == "ros":
            return "ros" if ROS_AVAILABLE else "error"
        return "ros" if ROS_AVAILABLE else "mock"

    # ROS-BACKEND
    def _run_ros(self):
        if not rclpy.ok():
            rclpy.init()
            self._ros_initialized_here = True

        self.node = Node("pyqt_hmi_node")

        self.node.create_subscription(Image, config.TOPIC_CAMERA_IMAGE, self._on_image, 10)
        self.node.create_subscription(JointState, config.TOPIC_JOINT_STATES, self._on_joint_states, 10)
        self.node.create_subscription(Float32, config.TOPIC_TRAIN_PROGRESS, self._on_progress, 10)
        self.node.create_subscription(Float32, config.TOPIC_CONFIDENCE, self._on_confidence, 10)
        self.node.create_subscription(Point, config.TOPIC_GRIP_POINT, self._on_grip_point, 10)
        self.node.create_subscription(String, config.TOPIC_HMI_STATE, self._on_state_msg, 10)
        self.node.create_subscription(String, config.TOPIC_HMI_LOG, self._on_log_msg, 10)

        self._cmd_pub = self.node.create_publisher(String, config.TOPIC_COMMAND, 10)
        self._twist_pub = self.node.create_publisher(Twist, config.TOPIC_CMD_VEL, 10)

        self.log_message.emit("ROS2-node gestart, luistert op de geconfigureerde topics.")
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

    def _on_progress(self, msg):
        self.progress_received.emit(float(msg.data))

    def _on_confidence(self, msg):
        self.confidence_received.emit(float(msg.data))

    def _on_grip_point(self, msg):
        self.grip_point_received.emit(float(msg.x), float(msg.y))

    def _on_state_msg(self, msg):
        self.state_changed.emit(msg.data)

    def _on_log_msg(self, msg):
        self.log_message.emit(msg.data)

    @staticmethod
    def _image_to_numpy(msg):
        #sensor_msgs/Image -> RGB numpy array, zonder cv_bridge nodig te hebben.
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
            else:
                return None  # onbekende encoding
        except Exception:
            return None

    # MOCK-BACKEND DEMO
    def _run_mock(self):
        self.state_changed.emit(self._mock_state)
        self.log_message.emit(
            "Robot niet gevonden. Demo-modus gestart!"
        )

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

        if self._mock_state == "autonomous":
            confidence = 0.65 + 0.28 * math.sin(t * 0.8)
        elif self._mock_state == "estop":
            confidence = 0.0
        else:
            confidence = 0.0
        self.confidence_received.emit(max(0.0, min(1.0, confidence)))

        if self._mock_state == "training":
            self._mock_progress = min(100.0, self._mock_progress + 1.2)
            if self._mock_progress >= 100.0:
                self.log_message.emit("[DEMO] Training voltooid.")
                self._set_mock_state("idle")
        self.progress_received.emit(self._mock_progress)

        gx = 0.5 + 0.18 * math.sin(t * 0.6)
        gy = 0.5 + 0.12 * math.cos(t * 0.9)
        self.grip_point_received.emit(gx, gy)

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

    # COMMANDO'S VANUIT DE GUI
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
        elif text == "start_autonomous" and self._mock_state != "estop":
            self._set_mock_state("autonomous")
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
