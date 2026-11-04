#!/bin/bash
# source env/env_notebook.sh   (notebooks -- ROS MELODIC)
# O IP do notebook (ROS_IP) e descoberto pela rota ate o robo; passe a
# interface como argumento se falhar:  source env/env_notebook.sh enp0s3
source /opt/ros/melodic/setup.bash
[ -f ~/catkin_ws/devel/setup.bash ] && source ~/catkin_ws/devel/setup.bash
export ROBOT_IP=192.168.1.100
if [ -n "$1" ]; then
  MY_IP=$(ip -4 addr show "$1" | awk '/inet /{print $2}' | cut -d/ -f1 | head -n1)
else
  MY_IP=$(ip route get "$ROBOT_IP" 2>/dev/null \
          | awk '{for(i=1;i<=NF;i++) if($i=="src") print $(i+1)}' | head -n1)
fi
if [ -z "$MY_IP" ]; then
  echo "Nao foi possivel descobrir o IP local. Passe a interface (ex.: enp0s3)."
  return 1 2>/dev/null || exit 1
fi
export MY_IP
unset ROS_HOSTNAME
export ROS_MASTER_URI=http://$ROBOT_IP:11311
export ROS_IP=$MY_IP
echo "ROS_MASTER_URI=$ROS_MASTER_URI  ROS_IP=$ROS_IP"
