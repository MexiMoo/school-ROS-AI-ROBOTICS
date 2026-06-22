#!/bin/bash
set -e
echo "=== Open Manipulator (Robot PC) Startup ==="
source /opt/ros/jazzy/setup.bash

cd /workspace
echo "[1/2] Building workspace..."
colcon build || true
source install/setup.bash

echo "[2/2] Starting bringup..."
ros2 launch open_manipulator_bringup omy_ai.launch.py
