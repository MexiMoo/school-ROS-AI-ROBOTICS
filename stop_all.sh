#!/bin/bash

ROBOT_HOST="root@omy-SNPR44B1011.local"

echo "ROS processen stoppen..."

docker exec open_manipulator pkill -9 -f ros2 2>/dev/null || true
docker exec physical_ai_server pkill -9 -f ros2 2>/dev/null || true

ssh "$ROBOT_HOST" 'docker exec open_manipulator pkill -9 -f ros2 2>/dev/null || true'
ssh "$ROBOT_HOST" 'reboot'

echo "Klaar, start script opnieuw uitvoeren..."
sleep 10
echo "Opnieuw proberen..."
sleep 10
echo "Opnieuw proberen..."
sleep 10
./start_omy.sh
