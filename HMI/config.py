import os

# HMI_MODE is de globale bit die bepaalt in welke modus de HMI start.
# Er zijn 3 mogelijke modi:
#
#   "auto" -> Gebruik ROS2 zodra rclpy beschiktbaar is, anders: demo-data
#   "mock" -> Forceer de demo-data modus
#   "ros"  -> Forceert ROS2, is rclpy er niet dan geeft de software een
#             error terug
#
# Override in de terminal:
#   HMI_MODE=mock python3 main.py
HMI_MODE = os.environ.get("HMI_MODE", "auto")

# ROS2 topics
TOPIC_CAMERA_IMAGE   = "/camera/image_raw"        # sensor_msgs/Image
TOPIC_JOINT_STATES   = "/joint_states"            # sensor_msgs/JointState
TOPIC_TRAIN_PROGRESS = "/training/progress"       # std_msgs/Float32  (0-100)
TOPIC_CONFIDENCE     = "/inference/confidence"    # std_msgs/Float32  (0-1)
TOPIC_GRIP_POINT     = "/vision/grip_point"       # geometry_msgs/Point (x,y genormaliseerd 0-1)
TOPIC_COMMAND        = "/hmi/command"             # std_msgs/String  (uitgaand, vanuit de HMI)
TOPIC_CMD_VEL        = "/cmd_vel"                 # geometry_msgs/Twist (optioneel jog)
TOPIC_HMI_STATE      = "/hmi/state"               # std_msgs/String  (inkomend: idle/recording/training/autonomous/estop)
TOPIC_HMI_LOG        = "/hmi/log"                 # std_msgs/String  (inkomend: vrije logregels voor het logboek)

# Text
APP_TITLE = "HMI (Homie Machine Interfaces)"
CELL_NAME = "Robotcel OMY-F3M"

# Logo: 200x60 px
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "logo.png")

# Hoofdaccentkleur
ACCENT_COLOR = "#00b8a9"