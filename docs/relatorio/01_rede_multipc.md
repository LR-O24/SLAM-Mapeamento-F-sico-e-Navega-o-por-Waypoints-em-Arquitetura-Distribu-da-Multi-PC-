# Relatorio — Configuracao da Rede Multi-PC (Etapa 1)

Dados coletados em 04/11/2026. Usar como base da secao "Configuracao da rede multi-PC".

## 1. Maquinas

| Papel | Hostname | IP | SO | ROS | Python |
|---|---|---|---|---|---|
| Robo / ROS Master (Aluno 1) | `pioneer` | 192.168.1.100 (wlan0) | Ubuntu 12.04.5 (i686) | Hydro | 2.7.3 |
| Notebook 1 — RViz (Aluno 2) | `Ubuntu1804` (VM VirtualBox) | 192.168.1.103 | Ubuntu 18.04.6 | Melodic | 2.7.17 |
| Notebook 2 — Diagnostico (Aluno 3) | a preencher | a preencher | | | |

Hydro e Melodic sao ROS 1 com as mesmas definicoes de mensagens usadas no projeto
(`sensor_msgs`, `nav_msgs`, `geometry_msgs`, `tf`, `move_base_msgs`, `actionlib_msgs`),
entao conversam no mesmo grafo. Os nos de SLAM/navegacao rodam so no robo.

## 2. Variaveis de ambiente

| Maquina | `ROS_MASTER_URI` | `ROS_IP` | Script |
|---|---|---|---|
| Robo | `http://192.168.1.100:11311` | 192.168.1.100 | `env/env_robot.sh` (ja definido no `.bashrc` do robo) |
| Notebooks | `http://192.168.1.100:11311` | detectado pela rota ate o robo | `env/env_notebook.sh` |

`ROS_HOSTNAME` e removido para evitar que o ROS anuncie nomes que as outras maquinas nao resolvem.

## 3. Validacao da comunicacao

| Teste | Resultado |
|---|---|
| `ping` robo -> Notebook 1 | 4/4 pacotes, 0% perda, RTT 3.7–24.2 ms (media 12.9 ms, Wi-Fi) |
| SSH Notebook 1 -> robo (`root@192.168.1.100`) | OK |
| `rostopic list` no Notebook 1 | Ve `/rosout`, `/rosout_agg` do Master no robo |
| `rostopic pub /teste_nb` (NB1) -> `rostopic echo` (robo) | Mensagens recebidas |
| `rostopic pub /teste_robo` (robo) -> `rostopic echo` (NB1) | Mensagens recebidas |

O teste nos dois sentidos e necessario porque o Master so faz a negociacao: os dados vao direto
entre as maquinas, entao o robo tambem precisa alcancar o IP do notebook (a VM esta em modo
que permite isso).

## 4. Sincronizacao de relogios (problema encontrado)

Medicao: `ssh root@192.168.1.100 'date +%s.%N'; date +%s.%N` e `ntpdate -q a.st1.ntp.br`.

| Momento | Observacao |
|---|---|
| Inicial | Robo 47.7 s atrasado em relacao ao Notebook 1; 41.8 s atrasado em relacao ao NTP.br |
| Apos `ntpdate -u` no robo | Robo passou a ficar ~20 s adiantado em ~8 min; diferenca crescia ~0.65 s a cada 8 s |
| Teste de 30 s contra NTP.br | Notebook 1: offset -0.0012 s -> -0.0013 s (estavel). Robo: -26.3 s -> -27.8 s (~4% rapido) |
| `service chrony stop` no robo | Deriva parou imediatamente (offset ficou em -27.84 s) |
| `ntpdate -u` com chrony parado | Robo: offset 0.00001 s -> 0.0003 s em 38 s (~8 ppm) |
| Final | Robo x Notebook 1: 0.020 s (inclui o tempo de retorno do SSH) |

**Causa:** o chrony do robo tem os servidores marcados `offline` (nunca sincroniza), mas aplica a
correcao de frequencia guardada em `chrony.drift`, acelerando o relogio. Com 4% de erro, a diferenca
passa de 1 s em menos de 30 s, o que inviabiliza TF/RViz entre as maquinas.

**Solucao adotada:** sem alterar a configuracao permanente do robo (compartilhado), no inicio de cada
sessao roda-se `env/sync_clock_robot.sh` no robo (para o chrony e acerta pelo NTP.br) e
`sudo ntpdate -u a.st1.ntp.br` em cada notebook.

## 5. Prints a anexar
- [ ] Terminal do robo com `roscore` rodando
- [ ] `rostopic list` no Notebook 1
- [ ] `rostopic pub`/`echo` nos dois sentidos
- [ ] Medicoes de relogio antes e depois
- [ ] Mesmos testes no Notebook 2
