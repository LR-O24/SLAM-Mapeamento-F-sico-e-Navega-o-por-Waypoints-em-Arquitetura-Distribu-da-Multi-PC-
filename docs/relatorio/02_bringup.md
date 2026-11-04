# Relatorio — Bringup do robo: RosAria + SICK LMS291 (Etapa 2)

Dados coletados em 04/11/2026 com `roslaunch pioneer_nav robot_bringup.launch` no robo.

## 1. Hardware detectado

| Item | Valor |
|---|---|
| Robo | Pioneer 3DX, subtipo `p3dx-sh`, nome `Ensino_4208` |
| Porta / baud do Pioneer | `/dev/ttyS0`, 9600 |
| Parametros do controlador | TicksMM = 128, DriftFactor = 0, RevCount = 16570 |
| LIDAR | SICK LMS 291-S05, `/dev/ttyS1`, 38400 bps |
| Configuracao do LIDAR | 180 graus, resolucao 1.0 grau (estava em 0.5 e o driver reconfigurou), modo 8 m / unidades em cm |

## 2. Topicos e frequencias

| Topico | Origem | Frequencia medida (`rostopic hz`) |
|---|---|---|
| `/scan` | `sicklms` | 9.37 Hz (desvio 0.5 ms) |
| `/odom` | RosAria (`/RosAria/pose` remapeado) | 10.00 Hz |
| `/cmd_vel` | assinado pelo RosAria (`/RosAria/cmd_vel` remapeado) | — |
| `/tf` | RosAria (`odom -> base_link`) + `static_transform_publisher` (`base_link -> laser`) | — |

`frame_id` do `/scan`: `laser`. O RosAria liga os motores automaticamente (`motors state 1`).

## 3. TF do laser

Medido com trena: centro do SICK 5 cm a frente do eixo das rodas e 30 cm acima do chao.
`base_link -> laser = (0.05, 0.0, 0.30)`, sem rotacao. Valores de trabalhos anteriores
(0.10–0.11 / 0.20–0.21) foram descartados por nao corresponderem a este robo.

## 4. Validacao visual (RViz no Notebook 1, `fixed_frame:=odom`)

- Paredes da arena aparecem retas; distancia entre paredes paralelas ~3.5 m (largura da arena).
- Teste de espelhamento: pessoa a esquerda do robo apareceu do lado do eixo +y (verde) do `base_link` -> laser **nao** invertido (`laser_inverted:=false`).
- TF `Status: Ok`, sem erros de extrapolacao (relogios sincronizados, ver `01_rede_multipc.md`).

## 5. Teleoperacao e checagem inicial da odometria

Teleop no Notebook 1 (`teleop.launch`, 0.2 m/s, 0.4 rad/s) -> `/cmd_vel` -> robo: sentidos corretos.

| Leitura `/odom` | x (m) | y (m) | yaw (graus) |
|---|---|---|---|
| Inicial | 1.512 | 0.024 | -6.0 |
| Apos reta | 3.678 | -0.213 | -8.1 |
| Apos giro de ~180 graus e retorno | 1.546 | 0.112 | 169.5 |

- Reta: 2.18 m segundo a odometria, compativel com a trena; desvio de -2.1 graus no yaw.
- Giro: 177.6 graus segundo a odometria (o giro manual nao foi exatamente 180 graus).
- Retorno: a odometria indica 0.09 m de distancia do ponto inicial.
- A pose inicial nao e zero porque o RosAria mantem a odometria acumulada desde que foi iniciado.

Esta e apenas uma checagem de sanidade; a analise quantitativa de drift e feita na Etapa 4
com `drift_logger.py` comparando `/odom` com a pose do SLAM.
