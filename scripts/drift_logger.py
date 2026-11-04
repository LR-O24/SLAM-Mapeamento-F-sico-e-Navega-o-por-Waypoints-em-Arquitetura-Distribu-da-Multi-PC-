#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Analise de drift da odometria (odom x SLAM/AMCL). Compativel com Python 2 (Hydro/Melodic).
Uso: rosrun pioneer_nav drift_logger.py   (com gmapping ou AMCL rodando)
 1) Posicione o robo na marca inicial e rode o script (registra o inicio).
 2) Teleopere o percurso e pare sobre a marca inicial.
 3) ENTER: compara odometria x map->base_link e pede o erro real (trena).
Resultados acumulados em drift_results.csv no diretorio atual."""
from __future__ import division, print_function
import math
import os
import rospy
import tf
from nav_msgs.msg import Odometry
from tf.transformations import euler_from_quaternion

try:
    ask = raw_input          # Python 2
except NameError:
    ask = input              # Python 3


def norm(a):
    return math.atan2(math.sin(a), math.cos(a))


def relative(p0, p1):
    """Pose p1 expressa no frame de p0. Poses = (x, y, yaw)."""
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    c, s = math.cos(-p0[2]), math.sin(-p0[2])
    return (c * dx - s * dy, s * dx + c * dy, norm(p1[2] - p0[2]))


class Drift(object):
    def __init__(self):
        self.odom = None
        self.path = 0.0
        self.last = None
        rospy.Subscriber("/odom", Odometry, self.cb)
        self.lis = tf.TransformListener()

    def cb(self, m):
        q = m.pose.pose.orientation
        p = (m.pose.pose.position.x, m.pose.pose.position.y,
             euler_from_quaternion([q.x, q.y, q.z, q.w])[2])
        if self.last is not None:
            self.path += math.hypot(p[0] - self.last[0], p[1] - self.last[1])
        self.last = p
        self.odom = p

    def slam_pose(self):
        self.lis.waitForTransform("map", "base_link", rospy.Time(0), rospy.Duration(3.0))
        tr, q = self.lis.lookupTransform("map", "base_link", rospy.Time(0))
        return (tr[0], tr[1], euler_from_quaternion(q)[2])

    def run(self):
        while self.odom is None and not rospy.is_shutdown():
            rospy.sleep(0.1)
        o0, s0 = self.odom, self.slam_pose()
        self.path = 0.0
        rospy.loginfo("Inicio registrado. Odom=%s SLAM=%s", str(o0), str(s0))
        trial = 0
        while not rospy.is_shutdown():
            ask("\nPercurso concluido? Pare sobre a marca e pressione ENTER... ")
            o1, s1 = self.odom, self.slam_pose()
            ro, rs = relative(o0, o1), relative(s0, s1)
            pos_err = math.hypot(ro[0] - rs[0], ro[1] - rs[1])
            yaw_err = math.degrees(norm(ro[2] - rs[2]))
            drift = 100.0 * pos_err / self.path if self.path > 0 else float("nan")
            print("Distancia percorrida (odom): %.3f m" % self.path)
            print("Deslocamento odom : x=%.3f y=%.3f yaw=%.1f deg"
                  % (ro[0], ro[1], math.degrees(ro[2])))
            print("Deslocamento SLAM : x=%.3f y=%.3f yaw=%.1f deg"
                  % (rs[0], rs[1], math.degrees(rs[2])))
            print("Erro odom vs SLAM: %.3f m | Drift: %.2f %% | Erro yaw: %.1f deg"
                  % (pos_err, drift, yaw_err))
            try:
                real = float(ask("Erro REAL com trena em m (ENTER p/ pular): ") or "nan")
            except ValueError:
                real = float("nan")
            trial += 1
            new = not os.path.exists("drift_results.csv")
            with open("drift_results.csv", "a") as f:
                if new:
                    f.write("trial,path_m,odom_dx,odom_dy,odom_yaw_deg,slam_dx,slam_dy,"
                            "slam_yaw_deg,pos_err_m,drift_pct,yaw_err_deg,real_err_tape_m\n")
                f.write("%d,%.3f,%.3f,%.3f,%.1f,%.3f,%.3f,%.1f,%.3f,%.2f,%.1f,%s\n" % (
                    trial, self.path, ro[0], ro[1], math.degrees(ro[2]),
                    rs[0], rs[1], math.degrees(rs[2]), pos_err, drift, yaw_err, real))
            print("Salvo em drift_results.csv (tentativa %d). Outra volta + ENTER, ou Ctrl+C." % trial)
            o0, s0, self.path = self.odom, self.slam_pose(), 0.0


if __name__ == "__main__":
    rospy.init_node("drift_logger", anonymous=True)
    Drift().run()
