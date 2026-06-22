#!/bin/bash
set -e

ROBOT_HOST="root@omy-SNPR44B1011.local"

echo "=== OMY Volledige Startup ==="

#Docker opzetten op de ROBOT PC
echo "[1/2] Robot PC: Open Manipulator container starten..."
ssh "$ROBOT_HOST" "cd /data/docker/open_manipulator && docker compose up -d"
echo "      Wachten tot robot bringup actief is..."
sleep 10

# Docker opzetten voor de AI op de LAPTOP
echo "[2/2] Laptop: Physical AI Tools container starten..."
cd ~/physical_ai_tools/docker

# Container starten
./container.sh start

# Camera's en AI server starten binnenin de container
./container.sh enter bash -c "
  source /opt/ros/jazzy/setup.bash
  source ~/ros2_ws/install/setup.bash 2>/dev/null || true

  echo 'Camera nodes starten...'
  ros2 launch realsense2_camera rs_multi_camera_launch.py \
      camera_name1:=cam_wrist serial_no1:=\"'_230322274265'\" device_type1:=d4 \
      camera_name2:=cam_top serial_no2:=\"'_233522071994'\" device_type2:=d4 &
  sleep 3

  ros2 launch realsense2_camera rs_launch.py \
      camera_name:=cam_side serial_no:=\"'_837212070319'\" device_type:=d4 &
  sleep 3

  echo 'Physical AI Server starten...'
  ros2 launch physical_ai_server physical_ai_server_bringup.launch.py &

  wait
"

echo "=== OMY volledig opgestart! ==="
