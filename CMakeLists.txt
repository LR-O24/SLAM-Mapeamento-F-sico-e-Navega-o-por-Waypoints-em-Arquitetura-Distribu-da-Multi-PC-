cmake_minimum_required(VERSION 2.8.3)
project(pioneer_nav)

find_package(catkin REQUIRED COMPONENTS rospy actionlib move_base_msgs nav_msgs geometry_msgs tf)

catkin_package()

install(PROGRAMS
  scripts/waypoint_navigator.py
  scripts/drift_logger.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

install(DIRECTORY launch config maps rviz
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
