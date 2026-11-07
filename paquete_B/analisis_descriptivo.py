"""
T10: descriptivo de las redes (general y por fase ENSO, 50 km).

Metricas por red: nodos, aristas, densidad, grado y fuerza medios, clustering medio,
transitividad, componente gigante, camino promedio y diametro (en la componente gigante).
Fuerza = suma de w_meses (red general) o w_prop (redes por fase).

Entradas: resultados/red_general_50km.graphml, red_<fase>_50km.graphml
Salidas : resultados/metricas_descriptivas_50km.csv, resultados/grado_fuerza_general_50km.csv,
          figs/distribucion_grado_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
RES, FIGS = BASE / "resultados", BASE / "figs"
FIGS.mkdir(exist_ok=True)

REDES = [("General", "red_general_50km.graphml", "weight"),
         ("El Nino", "red_El_Nino_50km.graphml", "w_prop"),
         ("La Nina", "red_La_Nina_50km.graphml", "w_prop"),
         ("Neutral", "red_Neutral_50km.graphml", "w_prop")]


def resumen(nombre, G, wcol):
    activos = [n for n in G if G.degree(n) > 0]
    H = G.subgraph(activos)
    gc = H.subgraph(max(nx.connected_components(H), key=len))
    grados = np.array([d for _, d in H.degree()])
    fuerza = np.array([d for _, d in H.degree(weight=wcol)])
    return {
        "red": nombre,
        "nodos_con_aristas": H.number_of_nodes(),
        "aislados": G.number_of_nodes() - H.number_of_nodes(),
        "aristas": H.number_of_edges(),
        "densidad": nx.density(H),
        "grado_medio": grados.mean(),
        "grado_max": grados.max(),
        "fuerza_media": fuerza.mean(),
        "clustering_medio": nx.average_clustering(H),
        "transitividad": nx.transitivity(H),
        "componentes": nx.number_connected_components(H),
        "gigante_nodos": gc.number_of_nodes(),
        "gigante_pct": gc.number_of_nodes() / G.number_of_nodes(),
        "camino_promedio": nx.average_shortest_path_length(gc),
        "diametro": nx.diameter(gc),
    }


filas, grafos = [], {}
for nombre, archivo, wcol in REDES:
    G = nx.read_graphml(RES / archivo)
    grafos[nombre] = (G, wcol)
    filas.append(resumen(nombre, G, wcol))
    print(f"{nombre}: listo")

tabla = pd.DataFrame(filas).round(4)
tabla.to_csv(RES / "metricas_descriptivas_50km.csv", index=False)
print(tabla.T.to_string(header=False))

# Grado y fuerza por municipio (red general), insumo para T13 y para el informe
G, _ = grafos["General"]
gf = pd.DataFrame({
    "cod": list(G.nodes),
    "mpio": [G.nodes[n]["mpio"] for n in G],
    "dpto": [G.nodes[n]["dpto"] for n in G],
    "meses_activos": [G.nodes[n]["meses_activos"] for n in G],
    "grado": [G.degree(n) for n in G],
    "fuerza": [G.degree(n, weight="weight") for n in G],
    "clustering": [nx.clustering(G, n) for n in G],
}).sort_values("grado", ascending=False)
gf.to_csv(RES / "grado_fuerza_general_50km.csv", index=False)


# Distribucion acumulada complementaria (CCDF) en escala log-log
def ccdf(x):
    x = np.sort(x[x > 0])
    return x, 1 - np.arange(len(x)) / len(x)


fig, axs = plt.subplots(1, 2, figsize=(11, 4.3))
colores = {"General": "#222222", "El Nino": "#c0392b", "La Nina": "#2471a3", "Neutral": "#7f8c8d"}
for nombre, (G, wcol) in grafos.items():
    k = np.array([d for _, d in G.degree()])
    x, y = ccdf(k)
    axs[0].loglog(x, y, ".", ms=3, color=colores[nombre], label=nombre.replace("Nino", "Niño").replace("Nina", "Niña"))
axs[0].set_xlabel("Grado k"); axs[0].set_ylabel("P(K ≥ k)")
axs[0].set_title("Distribución de grado (CCDF)")
axs[0].legend(fontsize=8)

f = gf["fuerza"].to_numpy()
x, y = ccdf(f)
axs[1].loglog(x, y, ".", ms=3, color="#222222")
axs[1].set_xlabel("Fuerza s (meses en común)"); axs[1].set_ylabel("P(S ≥ s)")
axs[1].set_title("Distribución de fuerza, red general")
for ax in axs:
    ax.grid(alpha=0.3, which="both", lw=0.4)
fig.tight_layout()
fig.savefig(FIGS / "distribucion_grado_50km.png", dpi=200)
print("Figura guardada")
