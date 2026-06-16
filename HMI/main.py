#!/usr/bin/env python3

#======================================================================================#
# Entrypoint voor de PyQt5 HMI.
#
# Werkt nu out-of-the-box ZONDER ROS2: als rclpy niet gevonden wordt, schakelt
# de app automatisch naar demo-modus met nep data.
#
# Gebruik:
#    python3 main.py                  # auto-detect (huidige situatie: demo)
#    HMI_MODE=mock python3 main.py    # forceer demo, ook als ROS2 wél draait
#    HMI_MODE=ros  python3 main.py    # forceer ROS2 (foutmelding als rclpy ontbreekt)
#
# Dependencies installeren:
#    pip install -r requirements.txt --break-system-packages
#======================================================================================#

import sys
from PyQt5.QtWidgets import QApplication

from ros_interface import RosWorker
from hmi_window import MainWindow

def main():
    app = QApplication(sys.argv)

    ros_worker = RosWorker()
    window = MainWindow(ros_worker)

    ros_worker.start()
    window.show()

    exit_code = app.exec_()

    ros_worker.shutdown()
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
