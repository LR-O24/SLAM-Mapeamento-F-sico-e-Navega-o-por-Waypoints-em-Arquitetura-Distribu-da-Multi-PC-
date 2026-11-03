# pioneer_nav — Pioneer 3DX + SICK LMS291-S05 (RS232), ROS 1 Noetic, Multi-PC

Pacote catkin com SLAM (gmapping), AMCL, move_base (DWA) e patrulha por waypoints.
**Tudo pesado roda no robo (via SSH); no notebook rodam apenas RViz, teleop e diagnostico.**

## 0. Versoes (robo = ROS Hydro, notebooks = ROS Melodic)
- **Robo (Hydro, Ubuntu 12.04, Python 2):** roda driver, LIDAR, gmapping, AMCL, move_base e patrulha.
- **Notebooks (Melodic, Ubuntu 18.04):** rodam so RViz, teleop e diagnostico.
- Os scripts sao Python 2 (`#!/usr/bin/env python`), `package.xml` em formato 1 e `CMakeLists` simples, para compilar nas duas versoes.
- As mensagens usadas (`sensor_msgs/LaserScan`, `nav_msgs/*`, `geometry_msgs/*`, `tf/tfMessage`, `move_base_msgs/*`, `actionlib_msgs/*`) sao compativeis entre Hydro e Melodic. Se aparecer "md5sum mismatch" em algum topico, rode `rostopic info <topico>` nos dois lados e me avise.
- **Nao rode nodes de navegacao nos notebooks**; so visualizacao. Misturar versoes de move_base/costmap_2d e a principal fonte de problemas.

## 1. Instalacao
**No robo (Hydro):**
```bash
sudo apt-get install ros-hydro-gmapping ros-hydro-amcl ros-hydro-map-server \
  ros-hydro-move-base ros-hydro-dwa-local-planner ros-hydro-navfn \
  ros-hydro-sicktoolbox-wrapper ros-hydro-teleop-twist-keyboard chrony
# RosAria (codigo-fonte; requer ARIA instalada)
cd ~/catkin_ws/src && git clone https://github.com/amor-ros-pkg/rosaria.git
cp -r /caminho/pioneer_nav ~/catkin_ws/src/
cd ~/catkin_ws && rosdep install --from-paths src --ignore-src --rosdistro hydro -y
catkin_make && source devel/setup.bash
sudo usermod -aG dialout $USER     # acesso as portas seriais (relogar)
```
Se algum pacote nao estiver no apt do Hydro (ex.: `sicktoolbox_wrapper`), compile do GitHub em `~/catkin_ws/src`.

**Nos notebooks (Melodic):**
```bash
sudo apt install ros-melodic-rviz ros-melodic-teleop-twist-keyboard ros-melodic-rqt-graph chrony
cd ~/catkin_ws/src && cp -r /caminho/pioneer_nav . && cd .. && catkin_make
```
(No notebook o pacote serve so para os launches `rviz`/`teleop` e o `nav.rviz`. Nao e necessario instalar os drivers.)

## 2. Rede Multi-PC
Edite os IPs em `env/env_robot.sh` e `env/env_notebook.sh` (eles ja fazem `source` do ROS correto) e de `source` em cada maquina.
Teste: `ping` nos dois sentidos, `rostopic list` no notebook. **Sincronize os relogios** (`chrony`) nas tres maquinas: diferenca de relogio causa erros de TF no RViz.
Se o notebook nao resolver o nome do robo, adicione `IP_ROBO hostname_robo` em `/etc/hosts` (e vice-versa).

## 3. LIDAR LMS291 (RS232)
- Baud de 9600/19200/38400 (500k so com RS422/USB). Padrao: 38400, 180 graus, 1.0 grau (~9 Hz). Com 0.5 grau cai para ~5 Hz.
- Descubra as portas: `ls -l /dev/serial/by-id/` e passe via `lidar_port:=` e `pioneer_port:=`.
- O driver pode demorar ate ~30 s para negociar a conexao (`connect_delay`). Confira com `rostopic hz /scan` e `rostopic echo -n1 /scan/header` (o `frame_id` deve ser `laser`; se for outro, altere `sensor_frame` em `config/costmap_common_params.yaml` e o nome no `static_transform_publisher`).
- Se o scan sair espelhado/invertido: `laser_inverted:=true`.
- Ajuste `laser_x/y/z` (posicao do LIDAR relativa ao centro do robo) em `robot_bringup.launch`.
- O LMS291 cobre so 180 graus a frente: o robo nao enxerga atras (cuidado nas rotacoes e recoveries).

## 4. Fase 1 — Mapeamento
Robo (SSH):
```bash
roscore &                                  # ou em outro terminal
roslaunch pioneer_nav mapping.launch pioneer_port:=/dev/ttyUSB0 lidar_port:=/dev/ttyUSB1
rosservice call /RosAria/enable_motors     # se os motores nao responderem
```
Notebook 1: `roslaunch pioneer_nav rviz.launch`
Notebook 2: `roslaunch pioneer_nav teleop.launch` (velocidade baixa, giros lentos, feche loops)
Salvar: `rosrun map_server map_saver -f $(rospack find pioneer_nav)/maps/arena`

Drift (no robo ou notebook, com SLAM rodando): `rosrun pioneer_nav drift_logger.py`
Gera `drift_results.csv` (distancia, erro odom x SLAM, drift %, erro de yaw, erro real medido). Faca 3+ voltas.

## 5. Fase 2 — Navegacao
Encerre o mapping. Robo:
```bash
roslaunch pioneer_nav robot_bringup.launch
roslaunch pioneer_nav navigation.launch init_x:=0 init_y:=0 init_a:=0
```
Notebook 1: RViz -> **2D Pose Estimate** na pose real; teleopere um pouco ate as particulas convergirem; teste **2D Nav Goal**.
Habilite os costmaps no RViz se quiser inspecionar footprint/inflacao.

## 6. Fase 3 — Patrulha
1. Descubra as coordenadas das marcas: leve o robo a cada uma e rode `rosrun tf tf_echo map base_link`.
2. Edite `config/waypoints.yaml` com (x, y, theta).
3. Com AMCL convergido: `roslaunch pioneer_nav patrol.launch`
4. Seguranca: Aluno 4 com o botao de emergencia; cancelar goal: `rostopic pub -1 /move_base/cancel actionlib_msgs/GoalID -- {}`

## Diagnostico (Notebook 2)
`rostopic hz /scan /odom`, `rosnode info /move_base`, `rqt_graph`, `rosrun tf view_frames`

## Ordem resumida
| # | Onde | Comando |
|---|------|---------|
| 1 | Robo | `roscore` |
| 2 | Robo | `roslaunch pioneer_nav robot_bringup.launch` |
| 3 | Robo | `roslaunch pioneer_nav navigation.launch` |
| 4 | NB1 | `roslaunch pioneer_nav rviz.launch` (+ 2D Pose Estimate) |
| 5 | NB2 | diagnostico / `roslaunch pioneer_nav teleop.launch` |
| 6 | Robo | `roslaunch pioneer_nav patrol.launch` |
