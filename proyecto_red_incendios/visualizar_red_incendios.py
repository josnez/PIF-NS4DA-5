"""
Visualización de la red de co-ocurrencia de incendios (municipios a < 50 km).

Uso en VS Code:
  1) Pon este archivo en la carpeta del proyecto. Los archivos de entrada pueden estar
     en esa carpeta o en subcarpetas (resultados/, limites_dane/); el script los busca solo:
       red_general_50km.graphml, red_El_Nino_50km.graphml, red_La_Nina_50km.graphml,
       red_Neutral_50km.graphml y el shapefile MGN_ADM_MPIO_GRAFICO.shp (con sus .shx, .dbf, .prj)
  2) pip install networkx matplotlib geopandas numpy
  3) python visualizar_red_incendios.py
Salidas (carpeta figs/), una imagen por separado:
  red_general_mapa.png, red_general_fuerzas.png, red_El_Nino.png, red_La_Nina.png, red_Neutral.png
"""
from pathlib import Path
import numpy as np
import networkx as nx
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

BASE = Path(__file__).resolve().parent
FIGS = BASE / "figs"
FIGS.mkdir(exist_ok=True)

W_MIN_GENERAL = 5        # red general: aristas con >= 5 meses en común
W_PROP_MIN_FASE = 0.03   # fases: co-actividad en >= 3 % de los meses de la fase
FASES = [("El_Nino", "El Niño"), ("La_Nina", "La Niña"), ("Neutral", "Neutral")]
XLIM, YLIM = (-79.6, -66.4), (-4.4, 13.6)    # San Andrés queda fuera del recuadro


def buscar(nombre):
    """Busca un archivo por nombre en la carpeta del script y sus subcarpetas."""
    hallados = list(BASE.rglob(nombre))
    if not hallados:
        raise FileNotFoundError(f"No encuentro '{nombre}' dentro de {BASE}")
    return hallados[0]


# --- Contorno departamental -------------------------------------------------------------
dptos = gpd.read_file(buscar("MGN_ADM_MPIO_GRAFICO.shp"))[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)


def mapa(ax, G, wkey, umbral, mcol, vmax, esc, wmax):
    """Dibuja el mapa de la red: nodos en el centroide, aristas podadas por umbral.
    Tamaño = meses con actividad; color = grado en la red dibujada."""
    dptos.plot(ax=ax, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4, zorder=1)
    H = nx.Graph()
    H.add_nodes_from(G.nodes(data=True))
    H.add_edges_from((u, v, d) for u, v, d in G.edges(data=True) if d[wkey] >= umbral)
    pos = {n: (d["lon"], d["lat"]) for n, d in G.nodes(data=True)}
    segs = [[pos[u], pos[v]] for u, v in H.edges()]
    lw = [0.6 + 2.2 * d[wkey] / wmax for _, _, d in H.edges(data=True)]
    ax.add_collection(LineCollection(segs, colors="#1a1a1a", linewidths=lw, alpha=0.7, zorder=2))
    nodos = sorted([n for n in G if G.nodes[n][mcol] > 0], key=lambda n: H.degree(n))  # mayor grado encima
    xy = np.array([pos[n] for n in nodos])
    sc = ax.scatter(xy[:, 0], xy[:, 1], s=[4 + esc * G.nodes[n][mcol] for n in nodos],
                    c=[H.degree(n) for n in nodos], cmap="viridis", vmin=0, vmax=vmax,
                    edgecolors="white", linewidths=0.3, alpha=0.9, zorder=3)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect(1 / np.cos(np.radians(4.5)))
    ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
    for s in ax.spines.values():
        s.set_visible(False)
    return sc, H, len(nodos)


def grado_max(G, wkey, umbral):
    return max(dict(nx.Graph([(u, v) for u, v, d in G.edges(data=True) if d[wkey] >= umbral]).degree()).values())



def figura_mapa(G, wkey, umbral, mcol, vmax, esc, wmax, titulo, archivo):
    fig, ax = plt.subplots(figsize=(8, 9.2), dpi=200)
    sc, H, n = mapa(ax, G, wkey, umbral, mcol, vmax, esc, wmax)
    detalle = f"{n} municipios activos · {H.number_of_edges():,} de {G.number_of_edges():,} aristas dibujadas".replace(",", ".")
    ax.set_title(f"{titulo}\n{detalle}", fontsize=10)
    fig.colorbar(sc, ax=ax, shrink=0.55, pad=0.01).set_label("Grado en la red dibujada", fontsize=8)
    fig.savefig(FIGS / archivo, bbox_inches="tight")
    return H


# --- Red general: mapa ---------------------------------------------------------------
G = nx.read_graphml(buscar("red_general_50km.graphml"))
wmax = max(d["weight"] for *_, d in G.edges(data=True))
H = figura_mapa(G, "weight", W_MIN_GENERAL, "meses_activos", grado_max(G, "weight", W_MIN_GENERAL), 0.4, wmax,
                f"Red de incendios, municipios a < 50 km (2002-2024); aristas con ≥ {W_MIN_GENERAL} meses en común",
                "red_general_mapa.png")

# --- Red general: layout de fuerzas (imagen aparte) ----------------------------------
Hg = H.subgraph([x for x in H if H.degree(x) > 0]).copy()
pos = nx.spring_layout(Hg, iterations=60, seed=42, k=0.15)
gr = np.array([Hg.degree(x) for x in Hg], dtype=float)
tam = 5 + (gr - gr.min()) / (gr.max() - gr.min()) * 110
fig, ax = plt.subplots(figsize=(9, 9), dpi=200)
nx.draw_networkx_edges(Hg, pos, ax=ax, alpha=0.35, width=0.6, edge_color="#333333")
nx.draw_networkx_nodes(Hg, pos, ax=ax, node_size=tam, node_color=gr, cmap="viridis", linewidths=0)
ax.set_title(f"Red de incendios, layout de fuerzas\n{Hg.number_of_nodes()} nodos, "
             f"{Hg.number_of_edges():,} aristas".replace(",", "."), fontsize=10)
ax.axis("off")
fig.savefig(FIGS / "red_general_fuerzas.png", bbox_inches="tight")

# --- Cada fase ENSO, una imagen por separado, misma escala -----------------------------
Gs = {f: nx.read_graphml(buscar(f"red_{f}_50km.graphml")) for f, _ in FASES}
gm = max(grado_max(g, "w_prop", W_PROP_MIN_FASE) for g in Gs.values())
wm = max(d["w_prop"] for g in Gs.values() for *_, d in g.edges(data=True))
for f, nombre in FASES:
    figura_mapa(Gs[f], "w_prop", W_PROP_MIN_FASE, "meses_activos_fase", gm, 0.8, wm,
                f"{nombre}: aristas con co-actividad en ≥ {W_PROP_MIN_FASE:.0%} de los meses de la fase",
                f"red_{f}.png")

print("Guardadas en figs/: red_general_mapa, red_general_fuerzas, red_El_Nino, red_La_Nina, red_Neutral (.png)")
plt.show()    # abre las ventanas (borra esta línea si solo quieres los PNG)