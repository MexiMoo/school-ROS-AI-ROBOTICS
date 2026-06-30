#!/bin/bash

NO_FORMAT="\033[0m"
GREEN="\033[38;5;47m"

ROBOT_HOST="root@omy-SNPR44B1011.local"

docker cp "HMI/"         physical_ai_server:/root/
#docker cp "HMI/config.py"         physical_ai_server:/root/HMI/config.py
#docker cp "HMI/hmi_window.py"     physical_ai_server:/root/HMI/hmi_window.py
#docker cp "HMI/main.py"           physical_ai_server:/root/HMI/main.py
#docker cp "HMI/ros_interface.py"  physical_ai_server:/root/HMI/ros_interface.py

dockers/open_manipulator/docker/container.sh start

docker exec -d open_manipulator bash -c "
  source /opt/ros/jazzy/setup.bash && \
  source /root/ros2_ws/install/setup.bash && \
  export ROS_DOMAIN_ID=30 && \
  ros2 launch realsense2_camera rs_multi_camera_launch.py \
  camera_name1:=cam_wrist serial_no1:='_230322274265' \
  depth_module.color_profile1:=480,270,30 \
  depth_module.depth_profile1:=480,270,30 \
  device_type1:=d4 \
  camera_name2:=cam_top serial_no2:='_837212070319' \
  depth_module.color_profile2:=480,270,30 \
  depth_module.depth_profile2:=480,270,30 \
  device_type2:=d4
"
echo -e "${GREEN}Started camera's!${NO_FORMAT} Starting AI-Server..."
sleep 3

dockers/physical_ai_tools/docker/container.sh start

docker exec -d physical_ai_server bash -c "
  source /opt/ros/jazzy/setup.bash && \
  source /root/ros2_ws/install/setup.bash && \
  export ROS_DOMAIN_ID=30 && \
  ros2 launch physical_ai_server physical_ai_server_bringup.launch.py
"
echo -e "${GREEN}Started AI-Server!${NO_FORMAT} Starting HMI..."
sleep 5

docker exec -d physical_ai_server bash -c "
  source /opt/ros/jazzy/setup.bash && \
  source /root/ros2_ws/install/setup.bash && \
  export ROS_DOMAIN_ID=30 && \
  pip3 install -r /root/HMI/requirements.txt && \
  ros2 node list && \
  python3 /root/HMI/main.py
"
echo -e "${GREEN}Started HMI!${NO_FORMAT} Starting Robot..."
sleep 3

ssh "$ROBOT_HOST" "/data/docker/open_manipulator/docker/container.sh start"
sleep 3

ssh "$ROBOT_HOST" "docker exec -i open_manipulator bash -lc '
  source /opt/ros/jazzy/setup.bash
  source /root/ros2_ws/install/setup.bash
  export ROS_DOMAIN_ID=30
  ros2 launch open_manipulator_bringup omy_f3m_follower_ai.launch.py ros2_control_type:=omy_f3m_smooth
'"