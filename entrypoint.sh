#entrypoint.sh
!/bin/bash

set -e

echo "Robotcel"

source /opt/ros/jazzy/setup.bash

cd /workspace

echo "Workspace bouwen"
colcon build || true

source install/setup.bash

echo "Robot aanzetten"
ros2 launch open_manipulator_bringup omy_ai.launch.py
