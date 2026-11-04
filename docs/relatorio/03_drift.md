# Relatorio — Analise de drift da odometria (Etapa 4)

Sessao de 04/11/2026, arena de 7 x 3.5 m, com `mapping.launch` (gmapping) rodando no robo e
`drift_logger.py` no Notebook 1. Dados brutos: `docs/drift/drift_results_2026-11-04.csv`.

## 1. Metodo

1. Marca de partida no chao (centro do eixo das rodas + linha de direcao).
2. `drift_logger.py` registra a pose inicial pela odometria pura (`/odom`) e pelo SLAM (`map -> base_link`).
3. Volta completa no perimetro por teleoperacao (~0.7–1 m das paredes, 0.2 m/s), parando sobre a marca.
4. No ENTER, o script calcula o deslocamento desde o inicio em cada referencia (no frame da pose inicial)
   e a diferenca entre elas:
   - erro de posicao = |deslocamento odom − deslocamento SLAM|
   - drift % = erro de posicao / distancia percorrida (integrada pela odometria)
   - erro de yaw = rotacao odom − rotacao SLAM
5. A trena mede a distancia real entre a marca e a posicao final, para validar o SLAM como referencia.

## 2. Resultados validos

| Volta | Distancia (m) | Odom: dx, dy (m) / yaw | SLAM: dx, dy (m) / yaw | Erro posicao (m) | Drift (%) | Erro yaw | Trena (m) |
|---|---|---|---|---|---|---|---|
| 1 | 17.70 | -0.003, -0.170 / -12.5° | 0.037, -0.006 / +5.2° | 0.169 | 0.95 | -17.7° | 0.001 |
| 2 | 17.64 | -0.062, 0.029 / -0.1° | -0.030, -0.017 / +8.3° | 0.056 | 0.32 | -8.3° | — |
| **Media** | 17.67 | | | **0.113** | **0.64** | **-13.0°** | |

Erro de yaw relativo a rotacao total de uma volta (360°): 4.9% na volta 1 e 2.3% na volta 2 (media 3.6%).

As tentativas 2, 3 e 5 do CSV sao invalidas: o ENTER foi pressionado sem percurso (distancia 0 ou
deslocamentos todos nulos). Na tentativa 2, a volta foi feita enquanto o script esperava o valor da
trena, entao a distancia foi somada mas as poses ja tinham sido lidas no inicio. O script foi corrigido
para ignorar ENTER com menos de 1 m de percurso e congelar distancia e poses no instante do ENTER.

## 3. Discussao

- **SLAM como referencia:** na volta 1 a trena mediu 1 mm entre a marca e a posicao final, e o SLAM
  indicou 3.7 cm; o erro do proprio SLAM fica na ordem de poucos centimetros, uma ordem de grandeza
  abaixo do erro da odometria.
- **O erro de orientacao domina.** Em translacao a odometria do Pioneer errou 0.3–1.0% da distancia,
  mas acumulou 8–18° de erro de yaw por volta. Esse erro vem principalmente dos 4 giros de ~90° nos
  cantos: no giro, as rodas escorregam lateralmente (slippage) e a diferenca entre o diametro efetivo
  das rodas e a distancia entre elas (bitola) faz o encoder superestimar ou subestimar a rotacao.
- **Efeito no longo prazo:** um erro de yaw se converte em erro de posicao que cresce com a distancia
  percorrida depois dele. Com ~13° por volta, depois de algumas voltas a odometria pura indicaria o robo
  fora da arena, por isso a navegacao precisa da correcao pelo LIDAR (AMCL).
- **Variacao entre voltas** (0.95% vs 0.32%) reflete a forma da teleoperacao (velocidade nos cantos,
  correcoes manuais), o que reforca a necessidade de mais repeticoes.
- **Possivel melhoria:** o RosAria leu `RevCount = 16570` e `DriftFactor = 0` do controlador; esses
  parametros calibram a rotacao e o desvio sistematico, e poderiam ser ajustados a partir destes dados.

## 4. Pendente

- [ ] Repetir com pelo menos mais 1 volta valida (meta: 3 voltas) e 1 tentativa de 2–3 voltas seguidas
- [ ] Prints do RViz antes e depois das voltas
