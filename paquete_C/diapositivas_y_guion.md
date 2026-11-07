# Diapositivas (T26) y guion (T27)

Máximo 10 diapositivas y 5 minutos. El guion está pensado para leerse a ritmo normal (~140 palabras por minuto) y repartido entre los tres. Las figuras están en `proyecto_red_incendios/figs/`, `paquete_B/figs/` y `paquete_C/figs/`.

| # | Diapositiva | Figura | Habla | Tiempo |
|---|---|---|---|---|
| 1 | Pregunta y datos | — | Josue | 0:30 |
| 2 | Cómo construimos la red | `red_general_mapa.png` (A) | Josue | 0:30 |
| 3 | Cómo es la red | `distribucion_grado_50km.png`, `modelos_nulos_50km.png` (B) | Julian | 0:30 |
| 4 | Regiones de riesgo | `mapa_comunidades_50km.png` (B) | Julian | 0:25 |
| 5 | Hubs vs. puentes | `hubs_vs_puentes_50km.png` (B) | Julian | 0:25 |
| 6 | El Niño vs. La Niña: mapas | `mapas_el_nino_la_nina_50km.png` (C) | Jairo | 0:30 |
| 7 | El Niño vs. La Niña: ¿es azar? | `permutacion_enso_50km.png` (C) | Jairo | 0:25 |
| 8 | Resiliencia | `resiliencia_50km.png` (C) | Jairo | 0:25 |
| 9 | Difusión SIR e inmunización | `sir_inmunizacion_50km.png`, `mapa_propagadores_50km.png` (C) | Josue | 0:35 |
| 10 | Conclusiones y recomendaciones | — | Josue | 0:25 |

Total: 4:40, con 20 s de margen. Si los paquetes quedaron repartidos de otra forma, cambien la columna "Habla"; lo ideal es que cada quien presente lo que analizó.

---

## 1. ¿Qué municipios conectan el riesgo de incendio en Colombia?
**En la diapositiva**
- ¿Qué municipios conectan el riesgo de incendio y cómo cambia entre El Niño y La Niña?
- Datos: 45.166 registros de incendios de IDEAM, 1.076 municipios, 2002–2024
- Fase ENSO de cada mes según el índice ONI de NOAA
- Grupo 5: Josue Núñez · Julian Maestre · Jairo Naranjo

**Guion**
> Los incendios forestales en Colombia no ocurren aislados: municipios vecinos suelen quemarse al mismo tiempo. Queremos saber qué municipios conectan ese riesgo y si el fenómeno de El Niño lo vuelve más conectado. Usamos los 45 mil registros de incendios de IDEAM entre 2002 y 2024, y la fase de El Niño o La Niña de cada mes según el índice ONI.

## 2. La red: municipios que se queman al mismo tiempo
**En la diapositiva**
- Nodo: municipio (centroide DIVIPOLA)
- Arista: dos municipios a menos de 50 km con incendios el mismo mes
- Peso: número de meses en que coinciden
- Una red general y una por fase: El Niño, La Niña, neutral
- Método basado en Ferreira et al. (2020) y Matta et al. (2026)

**Guion**
> Cada nodo es un municipio. Dos municipios se conectan si están a menos de 50 kilómetros y tuvieron incendios el mismo mes, y el peso es cuántos meses coincidieron. Así obtuvimos una red de 1.032 municipios y 10.609 aristas. Repetimos la construcción usando solo los meses de cada fase, para tener una red de El Niño, una de La Niña y una neutral.

## 3. Una red espacial muy agrupada
**En la diapositiva**
- Grado medio 21,5; clustering 0,55; la componente gigante abarca el 95 % de los municipios
- Clustering 13 a 25 veces mayor que en redes aleatorias, pero caminos 4 veces más largos
- No es un small-world típico: es una red espacial
- La co-ocurrencia es el doble de lo que daría solo la temporada seca

**Guion**
> La red está muy agrupada: si dos municipios comparten un vecino, es muy probable que también estén conectados entre sí. Comparada con redes aleatorias, el clustering es hasta 25 veces mayor, pero los caminos son cuatro veces más largos. Es una red espacial, no un mundo pequeño típico. Además, al barajar los años, la co-ocurrencia cae a la mitad: los vecinos coinciden en los mismos años, no solo en la misma temporada.

## 4. 16 regiones de riesgo que no siguen los departamentos
**En la diapositiva**
- Louvain: 16 comunidades, modularidad 0,77
- Siguen la geografía, no los límites departamentales
- Ejemplos: Cundinamarca–Tolima, Santander–Boyacá, Córdoba–Sucre–Antioquia–Bolívar

**Guion**
> Con el algoritmo de Louvain encontramos 16 regiones de riesgo, con una modularidad alta de 0,77. Siguen la geografía, pero cruzan los departamentos: por ejemplo, Cundinamarca con Tolima, o Santander con Boyacá. Eso sugiere que la prevención debería coordinarse por región, no por departamento.

## 5. Los hubs y los puentes son municipios distintos
**En la diapositiva**
- Hubs (más vecinos): altiplano cundiboyacense, como Samacá, Ventaquemada o Tunja
- Puentes (mayor intermediación): corredor Cesar–Magdalena Medio–Córdoba, como San Alberto o Sabana de Torres
- Ningún municipio es hub y puente a la vez

**Guion**
> Los municipios con más vecinos, los hubs, están todos en el altiplano cundiboyacense. Pero los que unen regiones, los puentes, están en otro lado: en el sur del Cesar, el Magdalena Medio y Córdoba, y tienen pocos vecinos. Ningún municipio es las dos cosas a la vez, y eso va a ser clave para las recomendaciones.

## 6. En El Niño, el riesgo se une en una sola red nacional
**En la diapositiva**
- El Niño: 92 % de los municipios en una sola componente
- La Niña: 56 %, partida en 13 grupos; el Caribe queda aislado
- En El Niño los puentes unen el Caribe con los Andes

**Guion**
> Ahora la pregunta central. En El Niño, el 92 por ciento de los municipios queda en una sola red conectada; en La Niña, solo el 56, y la red se parte en 13 grupos. Fíjense en el Caribe: en La Niña queda aislado, en naranja, y en El Niño se une a los Andes justamente a través de los puentes del Cesar y Córdoba.

## 7. La diferencia no es azar
**En la diapositiva**
- Prueba de permutación: 1.000 reasignaciones aleatorias de la fase de cada mes
- Tres versiones: libre, dentro del mismo mes calendario y dentro del mismo año
- Aristas, grado, componente gigante y clustering: p ≤ 0,002 en las tres versiones
- Mecanismo: 97 municipios activos por mes en El Niño contra 41 en La Niña

**Guion**
> ¿Podría ser casualidad? Reasignamos al azar la fase de cada mes mil veces, también dentro del mismo mes del año, para controlar la temporada seca, y dentro del mismo año, porque el reporte de IDEAM aumentó con el tiempo. En los tres casos, la diferencia observada es mayor que en todas las permutaciones. El mecanismo es la simultaneidad: en El Niño se queman más del doble de municipios a la vez, y como son vecinos, la red se une.

## 8. La red resiste fallas al azar, pero cae si se quitan los puentes
**En la diapositiva**
- Quitar el 5 % de los municipios por intermediación parte la gigante a la mitad
- Por grado o al azar hay que quitar cerca del 45 %
- La Niña es mucho más frágil

**Guion**
> Medimos la resiliencia quitando municipios uno por uno. Si se quitan al azar o por número de vecinos, hay que quitar casi la mitad para partir la red. Pero si se quitan los puentes, basta con el 5 por ciento. Los hubs del altiplano son redundantes; el punto débil de esta red espacial son los puentes.

## 9. El Niño lleva la red al umbral de propagación
**En la diapositiva**
- SIR mensual con parámetros calibrados con los datos: γ = 0,62 (episodios de 1,6 meses), β = 0,021
- El Niño queda justo por encima del umbral epidémico (T/T_c = 1,03); La Niña, por debajo (0,71)
- Brotes grandes: 7,2 % en El Niño, 0,4 % en La Niña
- Vacunar 50 hubs reduce el brote medio ~70 %; vacunar puentes, casi nada

**Guion**
> Por último simulamos la propagación con un modelo SIR. No elegimos los parámetros a mano: los calibramos con los datos. Un municipio se mantiene activo en promedio un mes y medio, y cada vecino activo aumenta en dos a tres puntos su probabilidad de activarse. Con los parámetros de El Niño, la red queda justo por encima del umbral de propagación; con los de La Niña, muy por debajo. Y aquí aparece un contraste: para achicar los brotes conviene proteger los hubs del altiplano, que es de donde salen los brotes más grandes; los puentes no reducen el brote, pero sí evitan que las regiones se conecten.

## 10. Conclusiones y recomendaciones
**En la diapositiva**
- El Niño conecta más el riesgo: la red pasa de regional a nacional
- Para reducir el tamaño de los brotes: proteger los hubs del altiplano cundiboyacense
- Para evitar que las regiones se conecten: vigilar los puentes del corredor Cesar–Magdalena Medio–Córdoba
- Usar el ONI como alerta temprana
- Limitación: co-ocurrencia no es propagación física del fuego

**Guion**
> En conclusión, El Niño sí conecta más el riesgo de incendio en Colombia: la red pasa de estar partida en regiones a ser una sola red nacional, y cruza el umbral en el que el riesgo puede propagarse. Recomendamos dos prioridades distintas: reforzar la prevención en el altiplano cundiboyacense para reducir el tamaño de los brotes, y vigilar el corredor Cesar–Magdalena Medio–Córdoba para que las regiones no se conecten. Y como El Niño se anuncia con meses de anticipación, el índice ONI puede servir como alerta temprana. Gracias.
