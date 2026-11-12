#!/usr/bin/env python
"""Navegador de patrulha: visita N waypoints via move_base, faz giro de 360 graus
em cada um e retorna a origem. Parametros em config/waypoints.yaml."""
from __future__ import division
import math
import rospy
import actionlib
from actionlib_msgs.msg import GoalStatus
from geometry_msgs.msg import Twist
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from tf.transformations import quaternion_from_euler


def norm(a):
    return math.atan2(math.sin(a), math.cos(a))


def parse_pose(p, name, deg):
    """Aceita [x, y, theta], [x, y] (theta = 0) ou {x: .., y: .., theta: ..}."""
    if isinstance(p, dict):
        if "x" not in p or "y" not in p:
            raise ValueError("%s = %s: faltam as chaves x e y" % (name, p))
        vals = [p["x"], p["y"], p.get("theta", p.get("yaw", 0.0))]
    elif isinstance(p, (list, tuple)) and len(p) in (2, 3):
        vals = list(p) + [0.0] * (3 - len(p))
    else:
        raise ValueError("%s = %s: use [x, y, theta] (3 valores; recebidos %s)"
                         % (name, p, len(p) if isinstance(p, (list, tuple)) else "?"))
    try:
        x, y, th = [float(v) for v in vals]
    except (TypeError, ValueError):
        raise ValueError("%s = %s: valores precisam ser numeros" % (name, p))
    return x, y, (math.radians(th) if deg else th)


def make_goal(x, y, yaw):
    g = MoveBaseGoal()
    g.target_pose.header.frame_id = "map"
    g.target_pose.header.stamp = rospy.Time.now()
    g.target_pose.pose.position.x = x
    g.target_pose.pose.position.y = y
    q = quaternion_from_euler(0, 0, yaw)
    g.target_pose.pose.orientation.x = q[0]
    g.target_pose.pose.orientation.y = q[1]
    g.target_pose.pose.orientation.z = q[2]
    g.target_pose.pose.orientation.w = q[3]
    return g


class Patrol:
    def __init__(self):
        deg = rospy.get_param("~theta_unit", "rad") == "deg"
        raw = rospy.get_param("~waypoints", [])
        if not isinstance(raw, list) or not raw:
            raise ValueError("~waypoints vazio ou nao e lista: %s" % (raw,))
        self.waypoints = [parse_pose(p, "waypoint %d" % i, deg)
                          for i, p in enumerate(raw, start=1)]
        self.origin = parse_pose(rospy.get_param("~origin", [0.0, 0.0, 0.0]), "origin", deg)
        rospy.loginfo("Waypoints (x, y, theta[rad]): %s | origem: %s",
                      ["(%.2f, %.2f, %.2f)" % w for w in self.waypoints],
                      "(%.2f, %.2f, %.2f)" % self.origin)
        self.spin_mode = rospy.get_param("~spin_mode", "goals")
        self.spin_speed = rospy.get_param("~spin_speed", 0.5)
        self.goal_timeout = rospy.get_param("~goal_timeout", 120.0)
        self.step_timeout = rospy.get_param("~spin_step_timeout", 30.0)
        self.cmd_pub = rospy.Publisher("/cmd_vel", Twist, queue_size=1)
        self.client = actionlib.SimpleActionClient("move_base", MoveBaseAction)
        rospy.on_shutdown(self.stop)

    def stop(self):
        try:
            self.client.cancel_all_goals()
            self.cmd_pub.publish(Twist())
        except Exception:
            pass

    def go_to(self, x, y, yaw, timeout):
        self.client.send_goal(make_goal(x, y, yaw))
        if not self.client.wait_for_result(rospy.Duration(timeout)):
            self.client.cancel_goal()
            rospy.logwarn("Timeout indo para (%.2f, %.2f, %.2f)", x, y, yaw)
            return False
        ok = self.client.get_state() == GoalStatus.SUCCEEDED
        if not ok:
            rospy.logwarn("Goal falhou (estado %d)", self.client.get_state())
        return ok

    def spin_goals(self, x, y, yaw0):
        for i in range(1, 5):
            if rospy.is_shutdown():
                return False
            if not self.go_to(x, y, norm(yaw0 + i * math.pi / 2), self.step_timeout):
                return False
        return True

    def spin_cmd_vel(self):
        t = Twist()
        t.angular.z = self.spin_speed
        end = rospy.Time.now() + rospy.Duration(2 * math.pi / self.spin_speed)
        rate = rospy.Rate(20)
        while rospy.Time.now() < end and not rospy.is_shutdown():
            self.cmd_pub.publish(t)
            rate.sleep()
        self.cmd_pub.publish(Twist())
        return True

    def inspect(self, x, y, yaw):
        if self.spin_mode == "cmd_vel":
            return self.spin_cmd_vel()
        return self.spin_goals(x, y, yaw)

    def run(self):
        rospy.loginfo("Aguardando move_base...")
        self.client.wait_for_server()
        rospy.loginfo("move_base conectado. Iniciando patrulha (%d pontos).",
                      len(self.waypoints))
        for i, (x, y, yaw) in enumerate(self.waypoints, start=1):
            if rospy.is_shutdown():
                return
            rospy.loginfo("Waypoint %d/%d: (%.2f, %.2f, %.2f)",
                          i, len(self.waypoints), x, y, yaw)
            if self.go_to(x, y, yaw, self.goal_timeout):
                rospy.loginfo("Waypoint %d alcancado. Inspecao 360.", i)
                self.inspect(x, y, yaw)
            else:
                rospy.logwarn("Waypoint %d falhou; seguindo para o proximo.", i)
        rospy.loginfo("Retornando a origem.")
        self.go_to(self.origin[0], self.origin[1], self.origin[2], self.goal_timeout)
        rospy.loginfo("Patrulha concluida.")


if __name__ == "__main__":
    rospy.init_node("waypoint_navigator")
    try:
        patrol = Patrol()
    except ValueError as e:
        rospy.logfatal("config/waypoints.yaml invalido: %s", e)
        raise SystemExit(1)
    patrol.run()
