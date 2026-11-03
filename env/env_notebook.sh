#!/bin/bash
# source env/env_notebook.sh   (notebooks -- ROS MELODIC). Ajuste os IPs:
source /opt/ros/melodic/setup.bash
[ -f ~/catkin_ws/devel/setup.bash ] && source ~/catkin_ws/devel/setup.bash
export ROBOT_IP=192.168.0.10
export MY_IP=192.168.0.20
export ROS_MASTER_URI=http://$ROBOT_IP:11311
export ROS_IP=$MY_IP
echo "ROS_MASTER_URI=$ROS_MASTER_URI  ROS_IP=$ROS_IP"
