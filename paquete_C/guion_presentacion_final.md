# Guion del video · Grupo5_Final_NS4DA.pptx

Duración estimada: **4:30** de lectura, más las pausas entre diapositivas (máximo 5:00). Está escrito para leerse a ritmo normal, unas 140 palabras por minuto. Cada quien presenta lo que analizó:

| Diapositivas | Quién | Tiempo |
|---|---|---|
| 1, 2 y 10 (pregunta, red y conclusiones) | [Integrante paquete A] | 1:30 |
| 3, 4 y 5 (estructura, comunidades, hubs y puentes) | [Integrante paquete B] | 1:10 |
| 6, 7, 8 y 9 (El Niño vs. La Niña, resiliencia, SIR) | Josue | 1:50 |

En *cursiva* va lo que conviene señalar en pantalla mientras se habla.

---

### 1. Red de incendios en Colombia · [Integrante A] · 0:20

> Hola, somos el grupo 5: Jairo Naranjo, Josue Núñez y Julian Maestre. Los incendios forestales en Colombia no ocurren aislados: municipios vecinos suelen quemarse al mismo tiempo. Nos preguntamos qué municipios conectan ese riesgo y si El Niño lo vuelve más conectado que La Niña.

### 2. La red · [Integrante A] · 0:35

> Usamos los 45 mil registros de incendios del IDEAM entre 2002 y 2024. Cada nodo es un municipio, ubicado en su centroide. Dos municipios se conectan si están a menos de 50 kilómetros y tuvieron incendios el mismo mes, y el peso es cuántos meses coincidieron. Así obtenemos una red de 1.032 municipios y 10.609 aristas. Con el índice ONI armamos además una red para El Niño, otra para La Niña y otra neutral.

*Señalar el mapa: el núcleo denso en el centro del país.*

### 3. Cómo es la red · [Integrante B] · 0:30

> La red está muy agrupada: su clustering es de 0,56, contra 0,02 a 0,04 en redes aleatorias equivalentes. Pero sus caminos son casi cuatro veces más largos. No es un mundo pequeño típico: es una red espacial. Además, si barajamos los años, la co-ocurrencia cae a la mitad. Los vecinos no solo coinciden en la temporada seca: coinciden en los mismos años, y eso ya apunta a El Niño.

*Señalar la línea roja, lejos de los puntos grises de los modelos nulos.*

### 4. Regiones de riesgo · [Integrante B] · 0:20

> Con el algoritmo de Louvain encontramos 16 comunidades, con una modularidad alta de 0,77. Son regiones de riesgo que siguen la geografía pero cruzan departamentos, como Cundinamarca con Tolima o Santander con Boyacá. Por eso la prevención debería coordinarse por región, no solo por departamento.

### 5. Hubs vs. puentes · [Integrante B] · 0:20

> Los hubs, los municipios con más vecinos, están todos en el altiplano cundiboyacense, como Samacá o Tunja. Los puentes, los que unen regiones, están en el Cesar, el Magdalena Medio y Córdoba, y tienen pocos vecinos. Ningún municipio es las dos cosas, y eso será clave más adelante.

*Señalar en el mapa los puntos azules (hubs) agrupados y los rombos rojos (puentes) al norte.*

### 6. El Niño vs. La Niña · Josue · 0:30

> Ahora, la pregunta central. Los dos mapas usan la misma escala. En El Niño, el 92 % de los municipios queda en una sola red conectada; en La Niña, solo el 56 %, partida en 13 grupos. Miren el Caribe: en La Niña queda aislado, en naranja, y en El Niño se une a los Andes justamente por los puentes del Cesar y Córdoba.

*Señalar el Caribe en naranja en el mapa de La Niña y los rombos del corredor en El Niño.*

### 7. ¿Es azar? · Josue · 0:30

> ¿Y si fuera casualidad? Para probarlo, repartimos al azar las etiquetas de El Niño y La Niña entre los meses. Si la fase no importara, la diferencia real se parecería a las repartidas.
>
> Lo hicimos de tres formas: libre, es decir solo entre meses del mismo mes del año, para descontar la temporada seca; y solo dentro del mismo año. 

Como podemos observar la línea roja está a la derecha de todos los histogramas: El Niño esta más conectado que La Niña por más de lo que el azar logró en mil intentos.
>
> La explicación es la simultaneidad: en El Niño se queman 97 municipios por mes; en La Niña, 41.

*Señalar los histogramas gris y azul centrados en cero, luego el naranja corrido a la derecha y, al final, la línea roja más allá de todos.*


### 8. Resiliencia · 0:45

> Luego quitamos municipios uno por uno y medimos cuánto queda de la red principal. Probamos tres estrategias: al azar, por hubs y por puentes.
>
> Al azar o por hubs, la gris y la azul van casi juntas: hay que quitar cerca del 45 % para partir la red. Por puentes, la roja cae de inmediato: con el 5 % la red queda a la mitad, y cada escalón es una región que se desconecta.
>
> Los hubs tienen tantos vecinos que, si uno falta, otro lo reemplaza. Por lo que el punto débil son los puentes, y en La Niña, que ya empieza partida, todo es más frágil.

*Señalar la gris y la azul juntas; luego la roja cayendo en escalones en el panel de la red general; al final, el panel de La Niña, que arranca en 56 %.*

### 9. Difusión SIR · 0:55

> Por último, simulamos un modelo SIR, de epidemias. Aqui en cada mes, un municipio activo puede activar a sus vecinos y luego se recupera. Calibramos los parámetros con los datos, un episodio dura mes y medio, y cada vecino activo sube en dos a tres puntos la probabilidad de activarse.
>
> Lo clave es el umbral, como el R inicial de una epidemia: cuando esta por debajo de 1 los brotes se apagan solos. El Niño queda justo encima, en 1,03; Y La Niña, en 0,71. Por eso solo en El Niño aparecen brotes de hasta el 18 % de los municipios.
>
> Y al vacunar 50 hubs se reduce el brote medio cerca de un 70%; para los puentes, no tanto, porque los brotes crecen en el altiplano, donde están los hubs.

*Señalar en el primer panel la cola rosada (El Niño) que llega lejos a la derecha; después, en los paneles de inmunización, la línea azul que baja y la roja que se queda arriba.*

### 10. Conclusiones · [Integrante A] · 0:35

> En conclusión, El Niño sí conecta el riesgo de incendio en Colombia: la red pasa de estar partida en regiones a ser casi una sola red nacional. Recomendamos dos prioridades: proteger los hubs del altiplano para reducir el tamaño de los brotes, y vigilar los puentes del corredor Cesar–Magdalena Medio–Córdoba para que las regiones no se conecten. Como El Niño se anuncia con meses de anticipación, el ONI puede servir de alerta temprana. Eso sí: una arista es co-ocurrencia, no propagación física del fuego. Gracias.

---

## Para la discusión oral

Preguntas que probablemente hagan, con la respuesta corta:

- **¿Por qué hubs y puentes dan resultados opuestos en resiliencia y en el SIR?** Responden objetivos distintos. Quitar puentes separa las regiones, pero no achica los brotes, porque cada región conserva su núcleo denso. Los brotes nacen y crecen en el altiplano, donde están los hubs.
- **¿Cómo eligieron β y γ?** Con los datos. γ es 1 menos la probabilidad de seguir activo al mes siguiente (0,35). β se estimó por máxima verosimilitud, comparando la probabilidad de activarse según cuántos vecinos estaban activos el mes anterior.
- **¿El Niño no tiene más incendios simplemente porque sí?** Sí, y ese es el mecanismo: más municipios activos a la vez. La permutación por año descarta que sea solo el aumento del reporte, y con la misma cantidad de actividad El Niño sigue teniendo el doble de aristas.
- **¿Por qué no es un mundo pequeño si σ > 1?** Porque el camino promedio es 4 veces el de una red aleatoria. Es una red espacial: muy agrupada a nivel local, con caminos largos entre regiones.
- **¿Una arista significa que el fuego pasó de un municipio a otro?** No. Significa que ambos tuvieron incendios el mismo mes, en buena parte por causas comunes como el clima.
