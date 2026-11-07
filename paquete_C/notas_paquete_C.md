# Paquete C: resultados (T14, T15, T16, T18)

Todo se corre sobre las redes de `proyecto_red_incendios/resultados/` (50 km) y usa los rankings de hubs y puentes de B. Orden: `comparacion_enso.py`, `mapas_enso.py`, `resiliencia.py`, `sir_inmunizacion.py`. Requiere `networkx pandas numpy scipy matplotlib geopandas igraph`.

## T16. Comparación El Niño vs. La Niña
Archivos: `metricas_por_fase_50km.csv`, `permutacion_enso_50km.csv`, figura `permutacion_enso_50km.png`.

| | El Niño | La Niña | Neutral |
|---|---|---|---|
| Meses con reporte | 79 | 77 | 117 |
| Municipios activos por mes | 97 | 41 | 56 |
| Aristas | 9.543 | 3.456 | 7.205 |
| Grado medio (todos los municipios) | 18,5 | 6,7 | 14,0 |
| Componente gigante | 92 % | 56 % | 82 % |
| Componentes (≥ 2 municipios) | 4 | 13 | 6 |
| Clustering medio | 0,55 | 0,48 | 0,52 |

**Prueba de permutación** (1.000 permutaciones de las etiquetas de fase entre meses; cada fase conserva su número de meses). Se corrieron tres versiones:
- **Libre:** cualquier mes puede recibir cualquier etiqueta.
- **Por mes calendario:** solo se baraja enero con enero, febrero con febrero, etc. Controla la estacionalidad.
- **Por año:** solo se baraja dentro del mismo año. Controla que el reporte de IDEAM crece mucho con el tiempo (2024 tiene ~9 veces los registros de 2002) y que los meses de El Niño caen en años de reporte alto (2015, 2019, 2023–24). Es la más exigente.

| Métrica (El Niño − La Niña) | Libre | Mes calendario | Año |
|---|---|---|---|
| Aristas | 0,001 | 0,001 | 0,001 |
| Grado medio | 0,001 | 0,001 | 0,001 |
| Componente gigante | 0,001 | 0,001 | 0,001 |
| Clustering medio | 0,001 | 0,001 | 0,002 |
| Componentes (menos = más conectada) | 0,016 | 0,007 | 0,066 |
| Aristas por municipio-mes | 0,155 | 0,159 | 0,004 |

(p-valores unilaterales; 0,001 es el mínimo posible con 1.000 permutaciones.)

- **Respuesta: sí, El Niño conecta más el riesgo.** La red de El Niño tiene casi el triple de aristas, y su componente gigante abarca el 92 % de los municipios contra el 56 % en La Niña. La diferencia no se explica por la estacionalidad ni por el aumento del reporte con los años.
- **Sin 2023–2024** (reporte atípico) el resultado se mantiene: gigante 85 % contra 55 %, todos los p ≤ 0,006 salvo "aristas por municipio-mes" en las permutaciones libre y por mes calendario.
- **El mecanismo es la simultaneidad.** En El Niño hay 97 municipios activos por mes, contra 41 en La Niña. Por cada municipio-mes activo, la ganancia en aristas es pequeña (1,24 contra 1,11) y no es significativa en la permutación libre. Es decir, El Niño no cambia tanto *cómo* se conectan los municipios, sino *cuántos* se queman a la vez, y como están cerca, eso los une en una sola red. Coincide con el análisis de actividad igualada de A (T08): con la misma cantidad de municipio-mes que La Niña, El Niño sigue teniendo ~2 veces sus aristas.
- En la figura, el nulo "por año" ya está corrido hacia la derecha: parte de la diferencia sí viene de los años de reporte alto. Aun así, el valor observado queda fuera de las 1.000 permutaciones.

## T18. Mapas El Niño vs. La Niña
Figura `mapas_el_nino_la_nina_50km.png`: misma escala en los dos mapas; color = componente conexa; rombos rojos = los 15 puentes de cada fase (de B).

- **El Niño:** casi todo el país activo queda en una sola componente (azul). El Caribe se une a la región Andina, y los puentes están justo en ese corredor: San Alberto, Río de Oro (Cesar), Sabana de Torres (Santander), Pueblo Nuevo (Córdoba), Ituango (Antioquia).
- **La Niña:** la red se parte. El Caribe (naranja), el Urabá–Córdoba (verde) y varios grupos de los Llanos quedan aislados del núcleo andino. Los puentes se mueven al eje del alto Magdalena y el Cauca: Natagaima, Prado (Tolima), Aipe (Huila), Almaguer (Cauca).

## T14. Resiliencia
Archivos: `resiliencia_resumen_50km.csv`, `resiliencia_curvas_50km.csv`, `resiliencia_orden_remocion_50km.csv`, figura `resiliencia_50km.png`.

Se quitan municipios uno a uno y se mide la componente gigante (S). AUC = área bajo la curva S(f): menor = la red se rompe más rápido (Schneider et al., 2011). Grado e intermediación se recalculan en cada paso.

| Red | Al azar | Por grado (hubs) | Por intermediación (puentes) |
|---|---|---|---|
| General | 0,427 | 0,371 | **0,093** |
| El Niño | 0,408 | 0,333 | **0,081** |
| La Niña | 0,213 | 0,089 | **0,025** |

- **Quitar puentes rompe la red; quitar hubs casi no.** En la red general basta quitar el 5 % de los municipios por intermediación (~52) para que la gigante caiga a la mitad. Por grado hay que quitar el 46 %, igual que al azar.
- Los hubs (Samacá, Ventaquemada, Guachetá…) están todos en el altiplano cundiboyacense, una zona tan densa que cada uno tiene muchos reemplazos. Los primeros puentes quitados son San Alberto, Pueblo Nuevo, Segovia, Ituango y Sabana de Torres: el corredor que une el Caribe con los Andes.
- La red es muy robusta a fallas al azar y frágil ante ataques dirigidos a puentes (Albert et al., 2000; Holme et al., 2002). A diferencia de las redes libres de escala, aquí el punto débil no son los hubs sino los puentes, porque es una red espacial.
- **La Niña es mucho más frágil** (AUC al azar 0,21): ya parte fragmentada.

## T15. Difusión SIR e inmunización
Archivos: `sir_parametros_50km.csv`, `sir_escenarios_50km.csv`, `sir_propagadores_50km.csv`, `sir_inmunizacion_50km.csv`, figuras `sir_inmunizacion_50km.png` y `mapa_propagadores_50km.png`.

### Justificación de los parámetros
Los parámetros no se eligieron a mano: se calibraron con la tabla municipio–mes, con paso de tiempo de **1 mes** (la resolución de los datos).

- **γ (recuperación) = 1 − P(activo en t+1 | activo en t).** Un municipio activo sigue activo al mes siguiente el 35 % de las veces, así que γ = 0,65 y un episodio dura en promedio 1,5 meses. Es la duración observada de los episodios de incendios, no un supuesto.
- **β (transmisión por vecino activo)** se estimó por máxima verosimilitud con el modelo P(activarse | k vecinos activos) = 1 − (1 − p₀)(1 − β)^k, usando 260.000 transiciones municipio–mes (municipio inactivo en t, observado en t+1). Los datos siguen bien ese modelo: la probabilidad de activarse pasa de 2,2 % sin vecinos activos a 5,2 % con uno, 7,3 % con dos y 9,3 % con tres. El ajuste da β = 0,020.
- Se calibró por separado con los meses de cada fase:

| | γ | Duración (meses) | β | T por arista | T / T_c |
|---|---|---|---|---|---|
| General | 0,65 | 1,5 | 0,020 | 0,030 | 0,93 |
| El Niño | 0,62 | 1,6 | 0,021 | 0,034 | **1,03** |
| La Niña | 0,71 | 1,4 | 0,017 | 0,023 | **0,71** |

T = β / (1 − (1 − β)(1 − γ)) es la probabilidad de que un municipio active a un vecino antes de dejar de estar activo. T_c = ⟨k⟩ / (⟨k²⟩ − ⟨k⟩) = 0,033 es el umbral epidémico de la red (Newman, 2002; Pastor-Satorras et al., 2015): por encima de él pueden aparecer brotes que abarcan una fracción grande de la red.

- **Limitaciones de la calibración:** β mezcla contagio real con causas comunes (dos vecinos se activan juntos porque comparten el mismo clima seco), así que es una cota superior del contagio. El SIR no incluye las activaciones espontáneas (p₀): mide solo el efecto de la estructura de la red. El umbral T_c es de campo medio; en una red tan agrupada y espacial el umbral real es algo mayor.
- Se agregó un escenario **hipotético β×2** (T/T_c = 2) para ver qué pasa si los brotes fueran mucho más grandes.

### Resultados
- **El Niño pone la red justo por encima del umbral epidémico; La Niña, muy por debajo.** Con los parámetros de El Niño, el 7,2 % de los brotes llega a más del 5 % de los municipios (los grandes promedian 10 %). Con los de La Niña solo el 0,4 %. Es una segunda forma de ver lo mismo que T16: El Niño vuelve "contagioso" el riesgo a escala regional.
- **Potencial propagador:** los municipios desde donde más se propaga un brote están todos en el altiplano cundiboyacense (Chinavita, Soracá, Cucunubá, Boyacá, Guachetá), con brotes medios de ~6 % de los municipios. Se correlaciona con el grado (Spearman 0,91), casi nada con la intermediación (0,18).
- **Inmunización:** vacunar hubs funciona mucho mejor que vacunar puentes.

| Brote medio (% de municipios) | Sin vacunar | 50 hubs | 50 puentes | 50 al azar | 100 hubs | 100 puentes |
|---|---|---|---|---|---|---|
| General | 0,68 | 0,26 | 0,69 | 0,55 | 0,23 | 0,63 |
| El Niño | 1,03 | 0,33 | 1,15 | 0,81 | 0,26 | 0,97 |
| El Niño β×2 | 8,93 | 4,34 | 8,89 | 7,76 | 1,76 | 6,68 |

- Vacunar 50 hubs reduce el brote medio en ~65–70 %. Vacunar puentes no lo reduce más que vacunar al azar, ni siquiera en el escenario β×2 (esperábamos que ahí los puentes sí importaran, y no fue así). Diferencias menores a ~0,15 puntos son ruido Monte Carlo (2.000 brotes por punto).

### Hubs vs. puentes: dos objetivos distintos
T14 y T15 parecen contradecirse, pero responden preguntas distintas:
- **Para que un brote sea más pequeño** (menos municipios afectados): proteger los **hubs** del altiplano. Ahí se concentran los brotes y es donde más vecinos hay para contagiar.
- **Para que las regiones no queden conectadas entre sí** (evitar que el riesgo pase del Caribe a los Andes): proteger los **puentes** del corredor Cesar–Magdalena Medio–Córdoba–Antioquia. Quitarlos parte la red en regiones, pero no achica los brotes, porque cada región sigue teniendo su propio núcleo denso.

## Para el informe
- **Respuesta a la pregunta:** El Niño conecta más el riesgo de incendio en Colombia. No porque cambie cómo se relacionan los municipios, sino porque muchos más se queman a la vez: la red pasa de estar partida en regiones (La Niña) a una sola red nacional (El Niño), y queda por encima del umbral en que el riesgo puede propagarse a escala regional.
- **Recomendaciones:**
  1. En años de El Niño, reforzar la prevención en el altiplano cundiboyacense: es donde se originan los brotes más grandes y donde vacunar tiene más efecto.
  2. Vigilar el corredor Cesar–Magdalena Medio–Córdoba–Antioquia en El Niño: son los puentes que unen el Caribe con los Andes.
  3. Usar el índice ONI como alerta temprana: cuando se anuncia El Niño, la red está a punto de cruzar el umbral.
- **Limitaciones:** co-ocurrencia no es propagación física del fuego; β incluye causas comunes; el reporte de IDEAM crece con los años (controlado con la permutación por año y la sensibilidad sin 2023–24); la intermediación y el SIR son sin pesos.

## Referencias nuevas (para la lista del informe)
- Albert, R., Jeong, H. y Barabási, A.-L. (2000). Error and attack tolerance of complex networks. *Nature*, 406, 378–382.
- Holme, P., Kim, B. J., Yoon, C. N. y Han, S. K. (2002). Attack vulnerability of complex networks. *Physical Review E*, 65, 056109.
- Newman, M. E. J. (2002). Spread of epidemic disease on networks. *Physical Review E*, 66, 016128.
- Pastor-Satorras, R., Castellano, C., Van Mieghem, P. y Vespignani, A. (2015). Epidemic processes in complex networks. *Reviews of Modern Physics*, 87, 925–979.
- Schneider, C. M., Moreira, A. A., Andrade, J. S., Havlin, S. y Herrmann, H. J. (2011). Mitigation of malicious attacks on networks. *PNAS*, 108(10), 3838–3841.
