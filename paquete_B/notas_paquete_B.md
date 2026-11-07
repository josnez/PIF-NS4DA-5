# Paquete B: resultados (T10–T13, T19)

Todo se corre sobre las redes de `resultados/` (50 km). Orden: `analisis_descriptivo.py`, `modelos_nulos.py`, `comunidades.py`, `hubs_puentes.py` (este último usa las comunidades).

## T10. Descriptivo
Archivo: `metricas_descriptivas_50km.csv`, figura `distribucion_grado_50km.png`.

| | General | El Niño | La Niña | Neutral |
|---|---|---|---|---|
| Municipios con aristas | 989 | 958 | 681 | 856 |
| Aristas | 10.609 | 9.543 | 3.456 | 7.205 |
| Grado medio | 21,5 | 19,9 | 10,1 | 16,8 |
| Clustering medio | 0,55 | 0,54 | 0,48 | 0,51 |
| Componente gigante | 95 % | 92 % | 56 % | 82 % |
| Camino promedio (gigante) | 9,8 | 9,8 | 10,1 | 12,0 |

- El grado medio de esta tabla se calcula solo sobre municipios con al menos una arista; en `resumen_redes_fase_50km.csv` se calculó sobre todos, por eso los valores son distintos.
- La distribución de grado no es de ley de potencias: cae rápido después de ~40 vecinos. Tiene sentido porque la red está limitada por la distancia (nadie puede tener vecinos a más de 50 km).
- En La Niña la red se fragmenta: 13 componentes y la gigante solo tiene el 56 % de los municipios.

## T11. Modelos nulos
Archivos: `nulo_estructura_50km.csv`, `nulo_temporal_50km.csv`, figura `modelos_nulos_50km.png`.

**Estructura** (20 réplicas):

| | Clustering | Camino promedio |
|---|---|---|
| Observada | 0,56 | 9,8 |
| Erdős–Rényi | 0,02 | 2,6 |
| Configuración | 0,04 | 2,6 |

- El clustering es 13 a 25 veces mayor que en los nulos, pero el camino también es casi 4 veces más largo. Formalmente sigma > 1 (3,4 contra configuración), pero no es un small-world típico: es una red espacial, muy agrupada a nivel local y con caminos largos entre regiones.

**Temporal** (200 réplicas, mismos pares a < 50 km, se desordena cuándo está activo cada municipio):

| | Aristas con ≥ 5 meses en común |
|---|---|
| Observada | 4.649 |
| Permutando años (se conserva la temporada) | ~2.308 (p95: 2.351) |
| Permutando meses | ~962 (p95: 991) |

- La co-ocurrencia observada es el doble de lo que daría solo la estacionalidad. Es decir, los municipios vecinos no solo coinciden por la temporada seca: coinciden en los **mismos años**, lo que apunta a un factor interanual como El Niño.

## T12. Comunidades
Archivos: `comunidades_general_50km.csv`, `resumen_comunidades_50km.csv`, `comunidades_por_red_50km.csv`, figura `mapa_comunidades_50km.png`.

- Louvain (peso w_jaccard, mejor de 30 semillas): **16 comunidades, modularidad Q = 0,77**.
- Las comunidades siguen la geografía pero no los límites departamentales: ARI = 0,52 y NMI = 0,74 contra departamento. Varias cruzan departamentos, por ejemplo Cundinamarca–Tolima (139 municipios), Santander–Boyacá (125), Córdoba–Sucre–Antioquia–Bolívar (98) y el Eje Cafetero con Valle (70).
- Por fase: El Niño tiene 15 comunidades y la mayor es de 140 municipios. La Niña tiene 27, más pequeñas (la mayor es de 96). En El Niño las regiones se juntan en bloques más grandes.

## T13. Hubs vs. puentes
Archivos: `centralidad_general_50km.csv`, `hubs_puentes_top15_50km.csv`, `puentes_por_fase_50km.csv`, figura `hubs_vs_puentes_50km.png`.

- **Hubs** (más vecinos): todos en el altiplano cundiboyacense, como Samacá, Ventaquemada, Guachetá, Tunja y Lenguazaque, con ~60 vecinos cada uno.
- **Puentes** (mayor intermediación): sur del Cesar, Magdalena Medio, bajo Cauca y Córdoba, como San Alberto, Sabana de Torres, Río de Oro, La Gloria, Ituango y Montelíbano. Tienen grado bajo (mediana 7) pero conectan la región Andina con el Caribe.
- **Ningún municipio es hub y puente a la vez.** La correlación de Spearman entre grado e intermediación es solo 0,25. Los puentes también tienen vecinos más repartidos entre comunidades (participación 0,20 contra 0,10 de los hubs).
- Por fase: solo 2 de los 15 puentes de El Niño están también entre los de La Niña. 13 aparecen solo en El Niño, casi los mismos de la red general. Ojo: en La Niña la componente gigante es más pequeña, así que parte de la diferencia viene de que la red está más fragmentada.

## Para el informe
- Prevención: los hubs muestran dónde hay más incendios simultáneos (el altiplano), pero los puentes muestran dónde se juntan regiones. Reforzar vigilancia en el corredor Magdalena Medio–Cesar–Córdoba en años de El Niño tendría más efecto sobre la conectividad de la red.
- Limitación: la intermediación es sin pesos y sobre la componente gigante; un municipio con pocos registros puede salir como puente si es el único enlace entre dos zonas.
