#!/bin/bash

set -e

ROBOT_HOST="root@omy-SNPR44B1011.local"

echo "OMY_f3m setup"

echo "camera setup"
cd ~/open_manipulator/docker

./container.sh start
./container.sh enter bash -c "

  source /opt/ros/jazzy/setup.bash

  ros2 launch realsense2_camera rs_multi_camera_launch.py \
    camera_name1:=cam_wrist serial_no1:=\"'_230322274265'\" \
    depth_module.color_profile1:=480,270,30 \
    depth_module.depth_profile1:=480,270,30 \
    device_type1:=d4 \
    camera_name2:=cam_top serial_no2:=\"'_837212070319'\" \
    depth_module.color_profile2:=480,270,30 \
    depth_module.depth_profile2:=480,270,30 \
    device_type2:=d4 &

  wait
"

sleep 5

echo "physical ai tools server opzetten"
cd ~/physical_ai_tools/docker

./container.sh start

./container.sh enter bash -c "
  source /opt/ros/jazzy/setup.bash

  source ~/ros2_ws/install/setup.bash 2>/dev/null || true

  ai_server &

  wait
"

sleep 5
echo "Open manipulator docker opzetten"
ssh "$ROBOT_HOST" "cd /data/docker/open_manipulator && ./docker/container.sh start"

ssh "$ROBOT_HOST" "./docker/container.sh enter bash -c 'source /opt/ros/jazzy/setup.bash && ros2 launch open_manipulator_bringup omy_ai.launch.py'"

echo "Robotcel opgestart"
echo "WebUI beschikbaar op: http://localhost/"
# Herinnering waar de WebUI te vinden is
echo "Debugging:            http://localhost:8080"
# Poort 8080 voor debugging en alle beschikbare nodes
