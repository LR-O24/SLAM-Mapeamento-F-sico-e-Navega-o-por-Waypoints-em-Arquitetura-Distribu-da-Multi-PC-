#!/bin/bash
# Rodar no robo (root) no inicio de CADA sessao:  bash env/sync_clock_robot.sh
# O chrony do robo fica "offline" (sem acesso aos servidores) e aplica uma
# correcao de frequencia errada (~4% rapido). Sem ele, o relogio do robo erra
# ~8 ppm (< 0.03 s/h). Paramos o chrony e acertamos a hora pelo NTP.br.
NTP_SERVER=${1:-a.st1.ntp.br}
service chrony stop
ntpdate -u "$NTP_SERVER"
ntpdate -q "$NTP_SERVER" | tail -1
