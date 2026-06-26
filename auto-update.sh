#!/bin/bash

#==================================#
#       Github auto updater        #
#                                  #
# Download de Github automatisch   #
# naar het lokale device en deelt  #
# de bestanden vervolgens goed in. #
#                                  #
#         Door: Max Rook           #
#==================================#

NO_FORMAT="\033[0m"
GREEN="\033[38;5;47m"
RED="\033[38;5;196m"
YELLOW="\033[38;5;11m"
BOLD="\033[1m"
WHITE="\033[38;5;15m"
BLUE="\033[48;5;12m"

echo -e "Starting the ${BOLD}${WHITE}${BLUE}school-ROS-AI-ROBOTICS${NO_FORMAT} project..."
echo Pulling latest version...

if [ -d "school-ROS-AI-ROBOTICS/.git" ]; then
    echo -e "${RED}Repo bestaat${NO_FORMAT} -> ${GREEN}Repo wordt geupdated...${NO_FORMAT}"
    echo Repo bestaat -> Repo wordt geupdated...
    cd school-ROS-AI-ROBOTICS || exit

    git fetch --all
    git reset --hard origin/main
    git clean -fd

else
    echo -e "${YELLOW}Repo downloaden...${NO_FORMAT}"
    echo Repo downloaden...
    git clone https://github.com/MexiMoo/school-ROS-AI-ROBOTICS
    cd school-ROS-AI-ROBOTICS || exit
fi
chmod +x run.sh

echo
echo -e "${GREEN}Done!${NO_FORMAT} Starting auto-run script..."
echo

./run.sh
