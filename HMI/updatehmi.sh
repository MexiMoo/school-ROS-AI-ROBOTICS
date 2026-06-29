#!/bin/bash

set -e

docker cp /home/student/school-ROS-AI-ROBOTICS/HMI/config.py physical_ai_server:/root/HMI/config.py
docker cp /home/student/school-ROS-AI-ROBOTICS/HMI/hmi_window.py physical_ai_server:/root/HMI/hmi_window.py
docker cp /home/student/school-ROS-AI-ROBOTICS/HMI/main.py physical_ai_server:/root/HMI/main.py
docker cp /home/student/school-ROS-AI-ROBOTICS/HMI/ros_interface.py physical_ai_server:/root/HMI/ros_interface.py