#!/bin/bash
# source env/env_robot.sh   (no PC embarcado do robo -- ROS HYDRO)
source /opt/ros/hydro/setup.bash
[ -f ~/catkin_ws/devel/setup.bash ] && source ~/catkin_ws/devel/setup.bash
export ROBOT_IP=192.168.1.100
unset ROS_HOSTNAME
export ROS_MASTER_URI=http://$ROBOT_IP:11311
export ROS_IP=$ROBOT_IP
echo "ROS_MASTER_URI=$ROS_MASTER_URI  ROS_IP=$ROS_IP"
