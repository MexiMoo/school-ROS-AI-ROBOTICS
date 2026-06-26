#!/bin/bash

ROBOT_HOST="root@omy-SNPR44B1011.local"

echo "OMY_f3m setup"

echo "camera setup"
cd ~/open_manipulator/docker/open_manipulator/docker

./container.sh start

docker exec -d open_manipulator bash -c "source /opt/ros/jazzy/setup.bash && source /root/ros2_ws/install/setup.bash && export ROS_DOMAIN_ID=30 && \
  ros2 launch realsense2_camera rs_multi_camera_launch.py \
  camera_name1:=cam_wrist serial_no1:="'_230322274265'" \
  depth_module.color_profile1:=480,270,30 \
  depth_module.depth_profile1:=480,270,30 \
  device_type1:=d4 \
  camera_name2:=cam_top serial_no2:="'_837212070319'" \
  depth_module.color_profile2:=480,270,30 \
  depth_module.depth_profile2:=480,270,30 \
  device_type2:=d4 
" 

echo ""
echo "Camera's zijn gestart!"
echo ""
sleep 3

echo "physical ai tools server opzetten"
cd
cd ~/physical_ai_tools/docker
./container.sh start

docker exec -d physical_ai_server bash -c "
  source /opt/ros/jazzy/setup.bash && source /root/ros2_ws/install/setup.bash && export ROS_DOMAIN_ID=30 && \
  source ~/ros2_ws/install/setup.bash 2>/dev/null || true && \
  ros2 launch physical_ai_server physical_ai_server_bringup.launch.py
"

sleep 5

docker exec -d physical_ai_server bash -c "
  source /opt/ros/jazzy/setup.bash && \
  source /root/ros2_ws/install/setup.bash && \
  export ROS_DOMAIN_ID=30 && \
  export DISPLAY=${DISPLAY} && \
  python3 /root/HMI/main.py
"

echo ""
echo "Web UI is gestart!"
echo ""
sleep 3
echo "Open manipulator docker opzetten"
ssh "$ROBOT_HOST" "
docker exec open_manipulator bash -lc '
set -e
source /opt/ros/jazzy/setup.bash
test -f /root/ros2_ws/install/setup.bash && source /root/ros2_ws/install/setup.bash
ros2 launch open_manipulator_bringup omy_f3m_follower_ai.launch.py ros2_control_type:=omy_f3m_smooth
'
"
echo "Robotcel opgestart"
echo ""
echo "WebUI beschikbaar op: http://localhost/"
# Herinnering waar de WebUI te vinden is
echo "Debugging:            http://localhost:8080"
# Poort 8080 voor debugging en alle beschikbare nodes