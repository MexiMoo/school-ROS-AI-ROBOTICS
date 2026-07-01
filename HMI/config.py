import os

# HMI_MODE is de globale bit die bepaalt in welke modus de HMI start.
#   "auto" -> Gebruik ROS2 zodra rclpy beschikbaar is, anders: demo-data
#   "mock" -> Forceer de demo-data modus
#   "ros"  -> Forceert ROS2, is rclpy er niet dan geeft de software een error
#
# Override in de terminal:
#   HMI_MODE=mock python3 main.py
HMI_MODE = os.environ.get("HMI_MODE", "auto")

# ── ROS2 topics ────────────────────────────────────────────────────────────────
# Camera draait lokaal op de laptop
TOPIC_CAMERA_IMAGE   = "/camera2/cam_top/color/image_raw"   # sensor_msgs/Image

# Robot hardware (komt van de robot via open_manipulator container)
TOPIC_JOINT_STATES   = "/joint_states"                      # sensor_msgs/JointState

# AI status (komt van physical_ai_server container op de laptop)
TOPIC_TASK_STATUS    = "/task/status"                       # physical_ai_interfaces/msg/TaskStatus
TOPIC_TRAINING       = "/training/status"                   # physical_ai_interfaces/msg/TrainingStatus
TOPIC_HF_STATUS      = "/huggingface/status"                # physical_ai_interfaces/msg/HFOperationStatus

# Collision detectie - NIET GEBRUIKT
#TOPIC_COLLISION      = "/collision_flag"                    # std_msgs/msg/Bool

# Grip point van vision (optioneel, als deze beschikbaar komt) - NIET GEBRUIKT
#TOPIC_GRIP_POINT     = "/vision/grip_point"                 # geometry_msgs/Point (x,y genormaliseerd 0-1)

# Commando's vanuit de HMI naar de robot
TOPIC_COMMAND        = "/hmi/command"                       # std_msgs/String
TOPIC_CMD_VEL        = "/cmd_vel"                           # geometry_msgs/Twist (optioneel jog)

# Task fases (uit TaskStatus.phase constanten)
TASK_PHASE = {
    0: "idle",        # READY
    1: "warming_up",  # WARMING_UP
    2: "resetting",   # RESETTING
    3: "recording",   # RECORDING
    4: "saving",      # SAVING
    5: "stopped",     # STOPPED
    6: "autonomous",  # INFERENCING
}

# Text
APP_TITLE = "HMI (Homie Machine Interfaces)"
CELL_NAME = "Robotcel OMY-F3M"

# Logo: 200x60 px
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")

# Hoofdaccentkleur
ACCENT_COLOR = "#00b8a9"

# Standaard model — wordt automatisch geselecteerd in de HMI dropdown
DEFAULT_POLICY_PATH = "/root/ros2_ws/src/physical_ai_tools/lerobot/outputs/train/Syntax-Terror-BV/FINAL"
