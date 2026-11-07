"""
T12: comunidades (Louvain) en la red general y en las redes por fase (50 km).

Peso: w_jaccard (meses en comun / meses en que al menos uno esta activo), para que los
municipios con muchos registros no dominen la particion. Se corre Louvain con 30 semillas
y se guarda la particion de mayor modularidad.
Comparacion con la division politica: ARI e NMI contra departamento y contra region natural
(region asignada por departamento, es una aproximacion).

Entradas: resultados/red_general_50km.graphml, red_<fase>_50km.graphml, limites_dane/
Salidas : resultados/comunidades_general_50km.csv, resultados/resumen_comunidades_50km.csv,
          resultados/comunidades_por_red_50km.csv, figs/mapa_comunidades_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from networkx.algorithms.community import louvain_communities, modularity
from sklearn.metrics import adjusted_rand_score, normalized_mutual_info_score
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
RES, FIGS = BASE / "resultados", BASE / "figs"
SEMILLAS = range(30)
TAM_MIN = 10            # comunidades con menos municipios se reportan como "pequenas"

REGION = {
    "ATLÁNTICO": "Caribe", "BOLÍVAR": "Caribe", "CESAR": "Caribe", "CÓRDOBA": "Caribe",
    "LA GUAJIRA": "Caribe", "MAGDALENA": "Caribe", "SUCRE": "Caribe",
    "ARCHIPIÉLAGO DE SAN ANDRÉS, PROVIDENCIA Y SANTA CATALINA": "Caribe",
    "ANTIOQUIA": "Andina", "BOYACÁ": "Andina", "CALDAS": "Andina", "CUNDINAMARCA": "Andina",
    "BOGOTÁ, D.C.": "Andina", "HUILA": "Andina", "NORTE DE SANTANDER": "Andina",
    "QUINDÍO": "Andina", "RISARALDA": "Andina", "SANTANDER": "Andina", "TOLIMA": "Andina",
    "CHOCÓ": "Pacífica", "CAUCA": "Pacífica", "NARIÑO": "Pacífica", "VALLE DEL CAUCA": "Pacífica",
    "ARAUCA": "Orinoquía", "CASANARE": "Orinoquía", "META": "Orinoquía", "VICHADA": "Orinoquía",
    "AMAZONAS": "Amazonía", "CAQUETÁ": "Amazonía", "GUAINÍA": "Amazonía", "GUAVIARE": "Amazonía",
    "PUTUMAYO": "Amazonía", "VAUPÉS": "Amazonía",
}


def mejor_louvain(G, peso):
    mejor = None
    for s in SEMILLAS:
        c = louvain_communities(G, weight=peso, seed=s)
        q = modularity(G, c, weight=peso)
        if mejor is None or q > mejor[1]:
            mejor = (c, q)
    return mejor


# ---------------------------------------------------------------- red general
G = nx.read_graphml(RES / "red_general_50km.graphml")
H = G.subgraph([n for n in G if G.degree(n) > 0])
com, q = mejor_louvain(H, "w_jaccard")
com = sorted(com, key=len, reverse=True)
etiqueta = {n: i + 1 for i, c in enumerate(com) for n in c}

df = pd.DataFrame({
    "cod": list(H.nodes),
    "mpio": [H.nodes[n]["mpio"] for n in H],
    "dpto": [H.nodes[n]["dpto"] for n in H],
    "lon": [H.nodes[n]["lon"] for n in H],
    "lat": [H.nodes[n]["lat"] for n in H],
    "comunidad": [etiqueta[n] for n in H],
})
df["region"] = df["dpto"].map(REGION)
df.to_csv(RES / "comunidades_general_50km.csv", index=False)

filas = []
for k, g in df.groupby("comunidad"):
    dptos = g["dpto"].value_counts()
    filas.append({
        "comunidad": k, "municipios": len(g),
        "dpto_principal": dptos.index[0], "pct_dpto_principal": round(dptos.iloc[0] / len(g), 3),
        "dptos_distintos": len(dptos),
        "region_principal": g["region"].value_counts().index[0],
        "departamentos": "; ".join(f"{d} ({v})" for d, v in dptos.head(4).items()),
    })
resumen = pd.DataFrame(filas)
resumen.to_csv(RES / "resumen_comunidades_50km.csv", index=False)

ari_d = adjusted_rand_score(df["dpto"], df["comunidad"])
nmi_d = normalized_mutual_info_score(df["dpto"], df["comunidad"])
ari_r = adjusted_rand_score(df["region"], df["comunidad"])
nmi_r = normalized_mutual_info_score(df["region"], df["comunidad"])
print(f"General: {len(com)} comunidades, Q = {q:.3f}")
print(f"  vs departamento: ARI = {ari_d:.3f}, NMI = {nmi_d:.3f}")
print(f"  vs region:       ARI = {ari_r:.3f}, NMI = {nmi_r:.3f}")
print(resumen.head(12).to_string(index=False))

# ---------------------------------------------------------------- por red
filas = [{"red": "General", "comunidades": len(com), "comunidades_ge10": sum(len(c) >= TAM_MIN for c in com),
          "mayor_comunidad": len(com[0]), "modularidad": q, "ARI_dpto": ari_d, "NMI_dpto": nmi_d}]
for fase in ["El_Nino", "La_Nina", "Neutral"]:
    F = nx.read_graphml(RES / f"red_{fase}_50km.graphml")
    F = F.subgraph([n for n in F if F.degree(n) > 0])
    c, qf = mejor_louvain(F, "w_jaccard")
    c = sorted(c, key=len, reverse=True)
    lab = {n: i for i, cc in enumerate(c) for n in cc}
    nodos = list(F.nodes)
    dpt = [F.nodes[n]["dpto"] for n in nodos]
    filas.append({"red": fase.replace("_", " "), "comunidades": len(c),
                  "comunidades_ge10": sum(len(x) >= TAM_MIN for x in c), "mayor_comunidad": len(c[0]),
                  "modularidad": qf, "ARI_dpto": adjusted_rand_score(dpt, [lab[n] for n in nodos]),
                  "NMI_dpto": normalized_mutual_info_score(dpt, [lab[n] for n in nodos])})
por_red = pd.DataFrame(filas).round(3)
por_red.to_csv(RES / "comunidades_por_red_50km.csv", index=False)
print(por_red.to_string(index=False))

# ---------------------------------------------------------------- mapa
shp = next(p for p in (BASE / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
dptos = gpd.read_file(shp)[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)

aristas = pd.read_csv(RES / "aristas_general_50km.csv", dtype={"cod_a": str, "cod_b": str})
aristas = aristas[aristas["w_meses"] >= 5]
pos = df.set_index("cod")[["lon", "lat"]]

top = resumen.sort_values("municipios", ascending=False).head(12)["comunidad"].tolist()
paleta = plt.get_cmap("tab20").colors
color = {k: paleta[i * 2 % 20] if i < 10 else paleta[(i * 2 + 1) % 20] for i, k in enumerate(top)}

fig, ax = plt.subplots(figsize=(8, 9.3))
dptos.plot(ax=ax, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4)
a = aristas[aristas.cod_a.isin(pos.index) & aristas.cod_b.isin(pos.index)]
for _, r in a.iterrows():
    ax.plot(*zip(pos.loc[r.cod_a], pos.loc[r.cod_b]), color="#555555", lw=0.3, alpha=0.18, zorder=2)
c = [color.get(k, "#c8c8c8") for k in df["comunidad"]]
ax.scatter(df["lon"], df["lat"], s=10, c=c, edgecolors="white", linewidths=0.2, zorder=3)
for k in top[:8]:
    g = df[df.comunidad == k]
    ax.annotate(str(k), (g["lon"].median(), g["lat"].median()), fontsize=9, weight="bold",
                ha="center", va="center", zorder=4,
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.75))
ax.set_xlim(-79.6, -66.4); ax.set_ylim(-4.4, 13.6)
ax.set_aspect(1 / np.cos(np.radians(4.5)))
ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title(f"Comunidades (Louvain) de la red general a < 50 km\n"
             f"{len(com)} comunidades · Q = {q:.2f} · en color las 12 más grandes", fontsize=10)
fig.tight_layout()
fig.savefig(FIGS / "mapa_comunidades_50km.png", dpi=200)
print("Figura guardada")
