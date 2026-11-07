"""
T18: mapas El Nino vs. La Nina lado a lado, con la misma escala.

Lo que se quiere mostrar es la diferencia de estructura que confirma la prueba de permutacion (T16):
en El Nino casi todos los municipios activos quedan en una sola componente conectada; en La Nina
la red se parte en muchos grupos regionales aislados.

Codificacion (igual en los dos mapas):
  - Posicion : centroide del municipio.
  - Color    : componente conexa. Azul = componente gigante; otros colores = componentes menores
               (>= 2 municipios); gris claro = municipio activo en la fase pero sin aristas.
  - Tamano   : meses con actividad dentro de la fase (misma escala en ambos mapas).
  - Lineas   : todas las aristas de la fase; el grosor crece con w_prop (proporcion de meses de la
               fase en que ambos municipios estan activos).
  - Rombos rojos: los 15 puentes (mayor intermediacion) de cada fase, calculados por B (T13).
Las lineas indican co-ocurrencia de registros en el mismo mes, no propagacion del fuego.

Entradas: ../proyecto_red_incendios/resultados/red_<fase>_50km.graphml,
          ../proyecto_red_incendios/limites_dane/ (capa MGN),
          ../paquete_B/resultados/puentes_por_fase_50km.csv
Salida  : figs/mapas_el_nino_la_nina_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D

BASE = Path(__file__).resolve().parent
A = BASE.parent / "proyecto_red_incendios"
B = BASE.parent / "paquete_B"
FIGS = BASE / "figs"
FIGS.mkdir(exist_ok=True)
RADIO_KM = 50
FASES = [("El Nino", "El Niño"), ("La Nina", "La Niña")]
XLIM, YLIM = (-79.6, -66.4), (-4.4, 13.6)      # San Andres queda fuera del recuadro
COLOR_GIGANTE = "#2f6db5"
COLORES_MENORES = ["#e8a33d", "#59a14f", "#b07aa1", "#9c755f", "#76b7b2", "#edc948", "#ff9da7",
                   "#8cd17d", "#d37295", "#a0cbe8", "#f1ce63", "#86bcb6", "#b6992d", "#d4a6c8"]
ESCALA_TAM = 2.2
N_ETIQUETAS = 4

shp = next(p for p in (A / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
dptos = gpd.read_file(shp)[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)
puentes = pd.read_csv(B / "resultados" / "puentes_por_fase_50km.csv", dtype={"cod": str})

redes = {f: nx.read_graphml(A / "resultados" / f"red_{f.replace(' ', '_')}_{RADIO_KM}km.graphml") for f, _ in FASES}
wmax = max(d["w_prop"] for G in redes.values() for _, _, d in G.edges(data=True))

fig, axes = plt.subplots(1, 2, figsize=(13, 8), dpi=200)
for ax, (f, nombre) in zip(axes, FASES):
    G = redes[f]
    dptos.plot(ax=ax, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4)
    pos = {n: (d["lon"], d["lat"]) for n, d in G.nodes(data=True)}

    # Aristas
    segs = np.array([[pos[u], pos[v]] for u, v in G.edges()])
    lw = 0.15 + 1.2 * np.array([d["w_prop"] for _, _, d in G.edges(data=True)]) / wmax
    ax.add_collection(LineCollection(segs, colors="#555555", linewidths=lw, alpha=0.25, zorder=2))

    # Componentes: color por componente, solo municipios activos en la fase
    activos = [n for n, d in G.nodes(data=True) if d["meses_activos_fase"] > 0]
    H = G.subgraph(activos)
    comps = sorted((c for c in nx.connected_components(H) if len(c) >= 2), key=len, reverse=True)
    color = {n: "#d0d0d0" for n in activos}
    for i, c in enumerate(comps):
        for n in c:
            color[n] = COLOR_GIGANTE if i == 0 else COLORES_MENORES[(i - 1) % len(COLORES_MENORES)]
    orden = sorted(activos, key=lambda n: G.nodes[n]["meses_activos_fase"])
    xy = np.array([pos[n] for n in orden])
    tam = 3 + ESCALA_TAM * np.array([G.nodes[n]["meses_activos_fase"] for n in orden])
    ax.scatter(xy[:, 0], xy[:, 1], s=tam, c=[color[n] for n in orden],
               edgecolors="white", linewidths=0.25, zorder=3)

    # Puentes de la fase (B, T13)
    pf = puentes[puentes.fase == f].sort_values("posicion")
    pxy = np.array([pos[c] for c in pf.cod])
    ax.scatter(pxy[:, 0], pxy[:, 1], s=46, marker="D", facecolors="none", edgecolors="#c0392b",
               linewidths=1.3, zorder=4)
    for i, r in enumerate(pf.head(N_ETIQUETAS).itertuples()):
        x, y = pos[r.cod]
        # Etiquetas alternadas a derecha e izquierda para que no se encimen
        ax.annotate(r.mpio.title(), (x, y), xytext=(6, 3) if i % 2 == 0 else (-6, -3),
                    textcoords="offset points", ha="left" if i % 2 == 0 else "right",
                    va="bottom" if i % 2 == 0 else "top", fontsize=7, color="#8e2a1f", zorder=5,
                    bbox=dict(boxstyle="round,pad=0.15", facecolor="white", edgecolor="none", alpha=0.75))

    n = G.number_of_nodes()
    gig = len(comps[0]) if comps else 0
    sin_aristas = sum(1 for v in activos if H.degree(v) == 0)
    ax.set_title(f"{nombre}\n{len(activos)} municipios activos · {G.number_of_edges():,} aristas\n"
                 f"Componente gigante: {100 * gig / n:.0f} % de los municipios · {len(comps)} componentes"
                 .replace(",", "."), fontsize=10)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect(1 / np.cos(np.radians(4.5)))
    ax.set_xticks([]); ax.set_yticks([])
    ax.set_xlabel(""); ax.set_ylabel("")
    for s in ax.spines.values():
        s.set_visible(False)
    print(f"{f}: activos={len(activos)}, aristas={G.number_of_edges()}, gigante={gig} ({100 * gig / n:.1f} %), "
          f"componentes>=2={len(comps)}, activos sin aristas={sin_aristas}")

# Leyendas comunes
items = [Line2D([], [], marker="o", ls="", markersize=7, markerfacecolor=COLOR_GIGANTE, markeredgecolor="white",
                label="Componente gigante"),
         Line2D([], [], marker="o", ls="", markersize=7, markerfacecolor=COLORES_MENORES[0], markeredgecolor="white",
                label="Componentes menores (un color cada una)"),
         Line2D([], [], marker="o", ls="", markersize=7, markerfacecolor="#d0d0d0", markeredgecolor="white",
                label="Activo, sin aristas"),
         Line2D([], [], marker="D", ls="", markersize=7, markerfacecolor="none", markeredgecolor="#c0392b",
                markeredgewidth=1.3, label="Puente de la fase (top 15 intermediación)")]
for v in (3, 15, 40):
    items.append(Line2D([], [], marker="o", ls="", markersize=np.sqrt(3 + ESCALA_TAM * v),
                        markerfacecolor="#9a9a9a", markeredgecolor="white", label=f"{v} meses activos"))
fig.legend(handles=items, loc="lower center", ncol=4, frameon=False, fontsize=8.5,
           bbox_to_anchor=(0.5, 0.03))
fig.suptitle(f"Red de co-ocurrencia de incendios por fase ENSO (municipios a menos de {RADIO_KM} km, 2002-2024)",
             fontsize=12, y=0.99)
fig.text(0.5, 0.005, "Misma escala de tamaño y grosor en los dos mapas. Línea = co-ocurrencia de registros en el mismo mes, "
         "no propagación. San Andrés queda fuera del recuadro.", ha="center", fontsize=7.5, color="#555")
fig.tight_layout(rect=(0, 0.11, 1, 0.97))
fig.savefig(FIGS / f"mapas_el_nino_la_nina_{RADIO_KM}km.png", bbox_inches="tight")
print("Guardado: figs/mapas_el_nino_la_nina_50km.png")
