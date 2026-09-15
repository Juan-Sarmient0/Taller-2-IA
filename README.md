# Taller 2 — Red Centinela

Proyecto de búsqueda local, optimización y juegos adversarios para ISIS-1611.

## Requisitos

- Python 3.11 o superior.
- Textual para la interfaz interactiva de terminal.
- Tkinter para la ventana gráfica. Si no está disponible, use `-t` o `-q`.

Instale la dependencia de la interfaz con:

```bash
python -m pip install -r requirements.txt
```

## Inicio rápido

```bash
python main.py
```

La interfaz permite seleccionar con el ratón o con `Tab` y `Enter`: punto,
escenario, modo de visualización, velocidad y perfil de búsqueda. En los
puntos de optimización también permite definir repeticiones y semilla. Use `R`
para ejecutar y `Q` para salir.

También puede ejecutar casos directamente:

```bash
python main.py -m optimization -a hillClimbing -l local_peak -x 0.55
python main.py -m optimization -a simulatedAnnealing -l risk_corridor --seed 7 --temperature 20 --cooling 0.97 -t
python main.py -m optimization -a geneticAlgorithm -l balanced_city --population 40 --generations 100 --mutation 0.05 -q
python main.py -m adversarial -a MinimaxAgent -l tiny_defense -d 2 -x 0.55
python main.py -m adversarial -a AlphaBetaAgent -l medium_defense -d 4 --max-rounds 40 -q
```

En búsqueda adversaria, la profundidad se mide en *plies*: cada acción de un
agente consume un nivel. `-d 1` explora solo una acción de `MAX`; `-d 2`
incluye una acción de `MAX` y la respuesta de `MIN`, es decir, una ronda
completa. El estado raíz no consume profundidad.

La ventana gráfica reproduce la ejecución como una secuencia de fotogramas.
En optimización resalta el módulo que sale y el que entra, descompone el
puntaje en cobertura, redundancia y exposición, e identifica mejoras,
deterioros aceptados y rechazos. En el algoritmo genético muestra un cruce
representativo por generación: padres, punto de corte, descendiente,
reparación y mutación; el mapa resalta todos los módulos que salen y entran
respecto al primer padre. En el juego dibuja el último movimiento de `MAX` o
`MIN`, las terminales activadas y las métricas acumuladas hasta ese turno.
Puede pausar, reiniciar o avanzar con los botones, las flechas del teclado, la
barra espaciadora y la tecla `R`.

## Archivos modificados por el estudiante

- `algorithms/optimization.py`: puntos 1, 2 y 3.
- `algorithms/adversarial.py`: puntos 4 y 5.
- `algorithms/evaluation.py`: función base entregada para el punto 4 y función
  heurística por completar en el punto 5.

El marcador `# TODO: Add your code here` identifica el lugar correspondiente a
cada implementación solicitada al estudiante.

`base_evaluation_function` se entrega completamente implementada para poder
desarrollar Minimax en el punto 4. En el punto 5 se completa
`evaluation_function`; tanto Minimax como alfa-beta usan esta misma función
activa para que sus decisiones puedan compararse bajo las mismas condiciones.

## Propósito de los mapas

Los escenarios están calibrados para que el comportamiento de los algoritmos sea observable:

- Optimización: `tiny_coverage` valida lo básico; `local_peak` contiene máximos locales; `plateau_grid` y `wide_plateau` presentan mesetas subóptimas; `redundant_modules` aísla la penalización por redundancia; `risk_corridor` y `exposure_tradeoff` contraponen cobertura y exposición; `barrier_districts` hace relevantes las distancias inducidas por los muros; `balanced_city` y `metropolitan_network` aumentan el espacio de búsqueda y contienen varias cuencas.
- Juego: `single_terminal` es el control; `tiny_defense`, `forked_routes` y `horizon_ambush` son sensibles a la profundidad; `bottleneck` exige anticipar una intercepción; `deceptive_distance` evidencia el efecto horizonte; `dual_terminal` cambia según el orden de objetivos; `medium_defense`, `loop_network` y `fortified_city` aumentan ciclos, rutas alternativas y ramificación para estudiar la poda.

En la simulación, el intruso ejecuta una política adversaria real: elige como raíz `MIN` mediante la misma función de evaluación, profundidad y orden de acciones del experimento. La salida reporta por separado los nodos explorados por el defensor y por el intruso.

Las ejecuciones repetidas de optimización reportan mejor puntaje, promedio,
desviación, evaluaciones promedio y tiempo promedio. Las ejecuciones
adversarias reportan profundidad, acción inicial, tipo de finalización, nodos
y tiempo; una derrota por intercepción se distingue de una finalización por
límite de rondas.

`nodes_evaluated` cuenta una vez cada estado procesado, incluida la raíz y los
estados terminales o de corte. La reducción producida por alfa-beta se observa
al comparar esta métrica con la obtenida por Minimax bajo las mismas condiciones.
