# pioneer_nav — Pioneer 3DX + SICK LMS291-S05 (RS232), ROS Hydro (robo) + Melodic (notebooks), Multi-PC

Pacote catkin com SLAM (gmapping), AMCL, move_base (DWA) e patrulha por waypoints.
**Tudo pesado roda no robo (via SSH); no notebook rodam apenas RViz, teleop e diagnostico.**

## 0. Versoes (robo = ROS Hydro, notebooks = ROS Melodic)
- **Robo (Hydro, Ubuntu 12.04, Python 2):** roda driver, LIDAR, gmapping, AMCL, move_base e patrulha.
- **Notebooks (Melodic, Ubuntu 18.04):** rodam so RViz, teleop e diagnostico.
- Os scripts sao Python 2 (`#!/usr/bin/env python`), `package.xml` em formato 1 e `CMakeLists` simples, para compilar nas duas versoes.
- As mensagens usadas (`sensor_msgs/LaserScan`, `nav_msgs/*`, `geometry_msgs/*`, `tf/tfMessage`, `move_base_msgs/*`, `actionlib_msgs/*`) sao compativeis entre Hydro e Melodic. Se aparecer "md5sum mismatch" em algum topico, rode `rostopic info <topico>` nos dois lados e me avise.
- **Nao rode nodes de navegacao nos notebooks**; so visualizacao. Misturar versoes de move_base/costmap_2d e a principal fonte de problemas.

## 1. Instalacao
**Robo (`root@pioneer`, 192.168.1.100, Hydro):** todas as dependencias ja estao instaladas
(o apt do Hydro nao existe mais): `rosaria` + ARIA, `sicktoolbox_wrapper`, `gmapping`
(em `/opt/ros/hydro`) e o stack `navigation` 1.11.14 compilado em `~/catkin_ws/src/navigation`.
O git do robo e antigo demais para o GitHub, entao o pacote e copiado a partir de um notebook:
```bash
# no notebook
scp -r ~/catkin_ws/src/pioneer_nav root@192.168.1.100:~/catkin_ws/src/
# no robo (ssh root@192.168.1.100)
cd ~/catkin_ws && catkin_make && source devel/setup.bash
```

**Nos notebooks (Melodic):**
```bash
sudo apt install ros-melodic-rviz ros-melodic-teleop-twist-keyboard ros-melodic-rqt-graph chrony
cd ~/catkin_ws/src && git clone https://github.com/LR-O24/SLAM-Mapeamento-F-sico-e-Navega-o-por-Waypoints-em-Arquitetura-Distribu-da-Multi-PC-.git pioneer_nav
cd ~/catkin_ws && catkin_make
```
(No notebook o pacote serve so para os launches `rviz`/`teleop` e o `nav.rviz`. Nao e necessario instalar os drivers.)

## 2. Rede Multi-PC
Robo = ROS Master em `192.168.1.100`. De `source` em `env/env_robot.sh` no robo e `env/env_notebook.sh`
nos notebooks (o IP do notebook e detectado automaticamente; eles ja fazem `source` do ROS correto).
Teste: `ping` nos dois sentidos, `rostopic list` no notebook e `rostopic pub`/`echo` nos dois sentidos.

**Relogios (inicio de CADA sessao).** Diferenca de relogio causa erros de TF no RViz.
O chrony do robo acelera o relogio (~4%) por estar sem acesso aos servidores; por isso ele e parado:
```bash
# robo (root)
bash ~/catkin_ws/src/pioneer_nav/env/sync_clock_robot.sh
# cada notebook (uma vez: sudo apt install ntpdate)
sudo ntpdate -u a.st1.ntp.br
# conferir no notebook: os dois numeros devem diferir < 0.3 s
ssh root@192.168.1.100 'date +%s.%N'; date +%s.%N
```
Se o notebook nao resolver o nome do robo, adicione `IP_ROBO hostname_robo` em `/etc/hosts` (e vice-versa).

## 3. LIDAR LMS291 (RS232)
- Baud de 9600/19200/38400 (500k so com RS422/USB). Padrao: 38400, 180 graus, 1.0 grau (~9 Hz). Com 0.5 grau cai para ~5 Hz.
- Portas no robo do laboratorio: Pioneer em `/dev/ttyS0` (9600 baud), LIDAR em `/dev/ttyS1`. Outras portas: `lidar_port:=` e `pioneer_port:=`.
- O driver pode demorar ate ~30 s para negociar a conexao (`connect_delay`). Confira com `rostopic hz /scan` e `rostopic echo -n1 /scan/header` (o `frame_id` deve ser `laser`; se for outro, altere `sensor_frame` em `config/costmap_common_params.yaml` e o nome no `static_transform_publisher`).
- Se o scan sair espelhado/invertido: `laser_inverted:=true`.
- Ajuste `laser_x/y/z` (posicao do LIDAR relativa ao centro do robo) em `robot_bringup.launch`.
- O LMS291 cobre so 180 graus a frente: o robo nao enxerga atras (cuidado nas rotacoes e recoveries).

## 4. Fase 1 — Mapeamento
Robo (SSH):
```bash
roscore &                                  # ou em outro terminal
roslaunch pioneer_nav mapping.launch
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
