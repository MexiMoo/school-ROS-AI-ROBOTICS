#!/bin/bash

ROBOT_HOST="root@omy-SNPR44B1011.local"

NO_FORMAT="\033[0m"
GREEN="\033[38;5;47m"

echo "ROS processen stoppen..."

docker exec open_manipulator pkill -9 -f ros2 2>/dev/null || true
docker exec physical_ai_server pkill -9 -f ros2 2>/dev/null || true

ssh "$ROBOT_HOST" 'docker exec open_manipulator pkill -9 -f ros2 2>/dev/null || true'
ssh "$ROBOT_HOST" 'reboot'

pkill -f rosbridge_websocket

echo "Alles is aan het herstarten, timer gestart. Wacht deze timer af i.v.m herstart tijd van de robot"
echo "Timer 30s gestart..."
sleep 30
echo -e "${GREEN}De robot kan nu opgestart worden!${NO_FORMAT} Gebruik ./start_omy.sh"
