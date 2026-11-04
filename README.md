# pioneer_nav — Pioneer 3DX com SICK LMS291-S05 (RS232), ROS 1, vários computadores

Este pacote catkin entrega mapeamento (gmapping), localização (AMCL), planejamento de trajetória (move_base com DWA) e patrulha entre pontos definidos.
**A carga computacional fica toda a bordo do robô, acessado por SSH. Os notebooks ficam só com visualização no RViz, controle manual e verificações de diagnóstico.**

## 0. Distribuições do ROS (robô com Hydro, notebooks com Melodic)

- **Robô (Hydro, Ubuntu 12.04, Python 2):** é onde rodam o driver, o sensor a laser, o gmapping, o AMCL, o move_base e a patrulha.
- **Notebooks (Melodic, Ubuntu 18.04):** ficam restritos ao RViz, ao teleop e às ferramentas de diagnóstico.
- Para que o pacote seja compilado em ambas as distribuições, os scripts estão em Python 2 (`#!/usr/bin/env python`), o `package.xml` segue o formato 1 e o `CMakeLists` foi mantido enxuto.
- Os tipos de mensagem empregados (`sensor_msgs/LaserScan`, `nav_msgs/*`, `geometry_msgs/*`, `tf/tfMessage`, `move_base_msgs/*`, `actionlib_msgs/*`) funcionam tanto no Hydro quanto no Melodic. Se surgir um "md5sum mismatch" em algum tópico, rode `rostopic info <topico>` no robô e no notebook e me envie o resultado.
- **Evite iniciar nodes de navegação nos notebooks**; use-os só para visualizar. Combinar versões diferentes de move_base/costmap_2d é a causa mais comum de falhas.

## 1. Instalação

**No robô (`root@pioneer`, 192.168.1.100, Hydro):** todas as dependências já estão instaladas
(o apt do Hydro não existe mais): `rosaria` + ARIA, `sicktoolbox_wrapper` e `gmapping` (em `/opt/ros/hydro`)
e o stack `navigation` 1.11.14 compilado em `~/catkin_ws/src/navigation`.
O git do robô é antigo demais para o GitHub, então o pacote é copiado a partir de um notebook:
```bash
# no notebook
scp -r ~/catkin_ws/src/pioneer_nav root@192.168.1.100:~/catkin_ws/src/
# no robô (ssh root@192.168.1.100). Use --pkg: outro pacote do workspace do robô
# (filtro_particulas_sakldmcl) não compila e interrompe o catkin_make completo.
cd ~/catkin_ws && catkin_make --pkg pioneer_nav && source devel/setup.bash
```

**Nos notebooks (Melodic):**
```bash
sudo apt install ros-melodic-rviz ros-melodic-teleop-twist-keyboard ros-melodic-rqt-graph ntpdate
cd ~/catkin_ws/src && git clone https://github.com/LR-O24/SLAM-Mapeamento-F-sico-e-Navega-o-por-Waypoints-em-Arquitetura-Distribu-da-Multi-PC-.git pioneer_nav
cd ~/catkin_ws && catkin_make
```
(Nos notebooks, o pacote só fornece os launches `rviz`/`teleop` e a configuração `nav.rviz`. Os drivers não precisam ser instalados.)

## 2. Configuração da rede entre as máquinas

O robô é o ROS Master em `192.168.1.100`. Execute `source env/env_robot.sh` no robô e `source env/env_notebook.sh`
nos notebooks (eles já carregam o ROS adequado a cada máquina; o IP do notebook é detectado automaticamente).

Para validar, faça `ping` de um lado para o outro, rode `rostopic list` no notebook e teste `rostopic pub`/`echo` nos dois sentidos.

**Relógios (no início de CADA sessão).** Horários diferentes geram erros de TF no RViz.
O chrony do robô acelera o relógio (~4%) por estar sem acesso aos servidores; por isso ele é parado:
```bash
# robô (root)
bash ~/catkin_ws/src/pioneer_nav/env/sync_clock_robot.sh
# cada notebook
sudo ntpdate -u a.st1.ntp.br
# conferir no notebook: os dois números devem diferir menos de 0.3 s
ssh root@192.168.1.100 'date +%s.%N'; date +%s.%N
```

Caso o notebook não consiga resolver o nome do robô, inclua `IP_ROBO hostname_robo` em `/etc/hosts` (e faça o mesmo, no sentido inverso, no robô).

## 3. Sensor LIDAR LMS291 (RS232)

- As velocidades de comunicação possíveis são 9600, 19200 e 38400 baud (500k exige RS422 ou USB). O ajuste padrão é 38400 baud, campo de 180 graus e passo angular de 1,0 grau, o que rende cerca de 9 Hz. Se o passo for 0,5 grau, a frequência desce para cerca de 5 Hz.
- Portas no robô do laboratório: Pioneer em `/dev/ttyS0` (9600 baud) e LIDAR em `/dev/ttyS1` (já são o padrão dos launches). Para outras portas, use `lidar_port:=` e `pioneer_port:=`.
- A negociação da conexão pelo driver pode demorar até ~30 s (parâmetro `connect_delay`). Confirme com `rostopic hz /scan` e `rostopic echo -n1 /scan/header`. O `frame_id` esperado é `laser`; se vier outro nome, modifique `sensor_frame` em `config/costmap_common_params.yaml` e também o nome usado no `static_transform_publisher`.
- Se a leitura aparecer espelhada ou de cabeça para baixo, passe `laser_inverted:=true`.
- Configure `laser_x/y/z`, que dão a posição do LIDAR em relação ao centro do robô, em `robot_bringup.launch`.
- Como o LMS291 varre só 180 graus na frente, a parte traseira do robô fica cega (atenção redobrada em giros e nos comportamentos de recovery).

## 4. Fase 1 — Construção do mapa

No robô (por SSH):
```bash
roscore &                                  # ou abra outro terminal para ele
roslaunch pioneer_nav mapping.launch
rosservice call /RosAria/enable_motors     # caso os motores não reajam
```
Notebook 1: `roslaunch pioneer_nav rviz.launch`

Notebook 2: `roslaunch pioneer_nav teleop.launch` (mantenha a velocidade baixa, faça giros lentos e complete os loops do percurso)

Gravação do mapa: `rosrun map_server map_saver -f $(rospack find pioneer_nav)/maps/arena`

Avaliação do drift (pode ser no robô ou no notebook, desde que o SLAM esteja ativo): `rosrun pioneer_nav drift_logger.py`

O resultado vai para `drift_results.csv`, com distância percorrida, discrepância entre odometria e SLAM, drift em %, erro de yaw e o erro real medido. Repita o percurso pelo menos 3 vezes.

## 5. Fase 2 — Navegação autônoma

Finalize o mapeamento e, no robô, execute:
```bash
roslaunch pioneer_nav robot_bringup.launch
roslaunch pioneer_nav navigation.launch init_x:=0 init_y:=0 init_a:=0
```
Notebook 1: no RViz, marque a posição verdadeira do robô com **2D Pose Estimate**; conduza-o manualmente por um trecho até que a nuvem de partículas se concentre; depois experimente o **2D Nav Goal**.

Se quiser examinar o footprint e a inflação, ative a exibição dos costmaps no RViz.

## 6. Fase 3 — Patrulha

1. Levante as coordenadas de cada marca: posicione o robô sobre ela e rode `rosrun tf tf_echo map base_link`.
2. Preencha `config/waypoints.yaml` com (x, y, theta) de cada ponto.
3. Quando o AMCL já tiver convergido, inicie: `roslaunch pioneer_nav patrol.launch`
4. Segurança: o Aluno 4 fica responsável pelo botão de emergência. Para interromper o goal atual, publique: `rostopic pub -1 /move_base/cancel actionlib_msgs/GoalID -- {}`

## Diagnóstico (Notebook 2)

`rostopic hz /scan /odom`, `rosnode info /move_base`, `rqt_graph`, `rosrun tf view_frames`

## Sequência resumida

| # | Local | Comando |
|---|-------|---------|
| 1 | Robô | `roscore` |
| 2 | Robô | `roslaunch pioneer_nav robot_bringup.launch` |
| 3 | Robô | `roslaunch pioneer_nav navigation.launch` |
| 4 | NB1 | `roslaunch pioneer_nav rviz.launch` (+ 2D Pose Estimate) |
| 5 | NB2 | diagnóstico / `roslaunch pioneer_nav teleop.launch` |
| 6 | Robô | `roslaunch pioneer_nav patrol.launch` |
