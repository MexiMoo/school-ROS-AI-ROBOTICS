#!/bin/bash
set -e

REPO_URL="https://github.com/MexiMoo/school-ROS-AI-ROBOTICS.git"
BRANCH="main"

echo "Syncing latest GitHub version..."

# workspace opzetten
mkdir -p workspace/src

cd workspace/src

if [ ! -d "repo" ]; then
    echo "Cloning repo..."
    git clone -b $BRANCH $REPO_URL repo
else
    echo "Pulling latest changes..."
    cd repo
    git pull origin $BRANCH
    cd ..
fi
