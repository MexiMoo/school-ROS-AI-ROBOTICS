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

if [ -d ".git" ]; then
    echo -e "${RED}Repo bestaat${NO_FORMAT} -> ${GREEN}Repo wordt geupdated...${NO_FORMAT}"
    
    git init
    git remote add origin https://github.com/MexiMoo/school-ROS-AI-ROBOTICS.git
    git fetch origin
    git checkout -B main origin/main
else
    echo -e "${YELLOW}Repo downloaden...${NO_FORMAT}"
    
    git init
    git remote add origin https://github.com/MexiMoo/school-ROS-AI-ROBOTICS.git
    git fetch origin
    git reset --hard origin/main
    git clean -fd
fi

echo
echo -e "${GREEN}Done!${NO_FORMAT} Starting auto-run script..."
echo

sudo chmod +x start_omy.sh
