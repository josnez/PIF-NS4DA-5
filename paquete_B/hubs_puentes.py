"""
T13: hubs vs. puentes en la red general (50 km) y puentes por fase ENSO.

Hub    : top 15 por grado (con cuantos municipios co-ocurre) y por fuerza (cuantos meses).
Puente : top 15 por intermediacion (betweenness, sin pesos, componente gigante).
Ademas se calcula el coeficiente de participacion de cada municipio respecto a las
comunidades de T12 (0 = todos sus vecinos estan en su comunidad; cerca de 1 = vecinos
repartidos en varias comunidades).

Entradas: resultados/red_general_50km.graphml, red_<fase>_50km.graphml,
          resultados/comunidades_general_50km.csv, limites_dane/
Salidas : resultados/centralidad_general_50km.csv, resultados/hubs_puentes_top15_50km.csv,
          resultados/puentes_por_fase_50km.csv, figs/hubs_vs_puentes_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from scipy.stats import spearmanr
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
RES, FIGS = BASE / "resultados", BASE / "figs"
TOP = 15

G = nx.read_graphml(RES / "red_general_50km.graphml")
gc = G.subgraph(max(nx.connected_components(G), key=len)).copy()
com = pd.read_csv(RES / "comunidades_general_50km.csv", dtype={"cod": str}).set_index("cod")["comunidad"]

bet = nx.betweenness_centrality(gc, normalized=True)


def participacion(n):
    k = gc.degree(n)
    if k == 0:
        return 0.0
    vc = pd.Series([com.get(v) for v in gc.neighbors(n)]).value_counts()
    return 1 - ((vc / k) ** 2).sum()


df = pd.DataFrame({
    "cod": list(gc.nodes),
    "mpio": [gc.nodes[n]["mpio"] for n in gc],
    "dpto": [gc.nodes[n]["dpto"] for n in gc],
    "lon": [gc.nodes[n]["lon"] for n in gc],
    "lat": [gc.nodes[n]["lat"] for n in gc],
    "comunidad": [com.get(n) for n in gc],
    "grado": [gc.degree(n) for n in gc],
    "fuerza": [gc.degree(n, weight="weight") for n in gc],
    "intermediacion": [bet[n] for n in gc],
    "participacion": [participacion(n) for n in gc],
})
df["rank_grado"] = df["grado"].rank(ascending=False, method="min").astype(int)
df["rank_intermediacion"] = df["intermediacion"].rank(ascending=False, method="min").astype(int)
df["hub"] = df["rank_grado"] <= TOP
df["puente"] = df["rank_intermediacion"] <= TOP
df.sort_values("intermediacion", ascending=False).round(5).to_csv(RES / "centralidad_general_50km.csv", index=False)

hubs = df.nlargest(TOP, "grado")
fuertes = df.nlargest(TOP, "fuerza")
puentes = df.nlargest(TOP, "intermediacion")
top = pd.DataFrame({
    "posicion": range(1, TOP + 1),
    "hub_grado": (hubs["mpio"] + " (" + hubs["dpto"] + ")").to_list(),
    "grado": hubs["grado"].to_list(),
    "hub_fuerza": (fuertes["mpio"] + " (" + fuertes["dpto"] + ")").to_list(),
    "fuerza": fuertes["fuerza"].to_list(),
    "puente": (puentes["mpio"] + " (" + puentes["dpto"] + ")").to_list(),
    "intermediacion": puentes["intermediacion"].round(4).to_list(),
    "grado_del_puente": puentes["grado"].to_list(),
})
top.to_csv(RES / "hubs_puentes_top15_50km.csv", index=False)

comun = set(hubs["cod"]) & set(puentes["cod"])
rho, _ = spearmanr(df["grado"], df["intermediacion"])
print(top.to_string(index=False))
print(f"\nMunicipios que son hub y puente a la vez: {len(comun)} de {TOP}")
print(f"Spearman grado vs intermediacion: {rho:.3f}")
print(f"Grado mediano de los puentes: {puentes['grado'].median():.0f} | de los hubs: {hubs['grado'].median():.0f}")
print(f"Participacion media: puentes {puentes['participacion'].mean():.3f} | hubs {hubs['participacion'].mean():.3f} "
      f"| todos {df['participacion'].mean():.3f}")

# ---------------------------------------------------------------- puentes por fase
filas = []
for fase in ["El_Nino", "La_Nina", "Neutral"]:
    F = nx.read_graphml(RES / f"red_{fase}_50km.graphml")
    F = F.subgraph(max(nx.connected_components(F), key=len))
    b = pd.Series(nx.betweenness_centrality(F, normalized=True)).nlargest(TOP)
    for i, (n, v) in enumerate(b.items(), 1):
        filas.append({"fase": fase.replace("_", " "), "posicion": i, "cod": n, "mpio": F.nodes[n]["mpio"],
                      "dpto": F.nodes[n]["dpto"], "intermediacion": round(v, 4)})
pf = pd.DataFrame(filas)
pf["puente_en_general"] = pf["cod"].isin(puentes["cod"])
pf.to_csv(RES / "puentes_por_fase_50km.csv", index=False)
nino = set(pf.loc[pf.fase == "El Nino", "cod"])
nina = set(pf.loc[pf.fase == "La Nina", "cod"])
print(f"\nPuentes top {TOP} en El Nino y en La Nina a la vez: {len(nino & nina)}")
solo = pf[(pf.fase == "El Nino") & ~pf.cod.isin(nina)]
print("Puentes que solo aparecen en El Nino:", ", ".join(solo["mpio"] + " (" + solo["dpto"] + ")"))

# ---------------------------------------------------------------- figura
shp = next(p for p in (BASE / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
dptos = gpd.read_file(shp)[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)

fig = plt.figure(figsize=(13, 6.6))
ax1 = fig.add_subplot(1, 2, 1)
ax1.scatter(df["grado"], df["intermediacion"], s=8, color="#b0b0b0", alpha=0.7, label="Municipios")
ax1.scatter(hubs["grado"], hubs["intermediacion"], s=30, color="#2471a3", label=f"Hubs (top {TOP} grado)")
ax1.scatter(puentes["grado"], puentes["intermediacion"], s=30, color="#c0392b", marker="D",
            label=f"Puentes (top {TOP} intermediación)")
for _, r in puentes.head(6).iterrows():
    ax1.annotate(r["mpio"].title(), (r["grado"], r["intermediacion"]), fontsize=7, xytext=(4, 2),
                 textcoords="offset points")
ax1.set_xlabel("Grado"); ax1.set_ylabel("Intermediación (normalizada)")
ax1.set_title(f"Grado vs. intermediación (Spearman = {rho:.2f})")
ax1.legend(fontsize=8); ax1.grid(alpha=0.3, lw=0.4)

ax2 = fig.add_subplot(1, 2, 2)
dptos.plot(ax=ax2, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4)
ax2.scatter(df["lon"], df["lat"], s=4, color="#c8c8c8", zorder=2)
ax2.scatter(hubs["lon"], hubs["lat"], s=40, color="#2471a3", edgecolors="white", lw=0.4, zorder=3, label="Hubs")
ax2.scatter(puentes["lon"], puentes["lat"], s=40, color="#c0392b", marker="D", edgecolors="white", lw=0.4,
            zorder=4, label="Puentes")
ax2.set_xlim(-79.6, -66.4); ax2.set_ylim(-4.4, 13.6)
ax2.set_aspect(1 / np.cos(np.radians(4.5)))
ax2.set_xticks([]); ax2.set_yticks([]); ax2.set_xlabel(""); ax2.set_ylabel("")
for s in ax2.spines.values():
    s.set_visible(False)
ax2.legend(loc="lower left", fontsize=8)
ax2.set_title("Ubicación de hubs y puentes")
fig.tight_layout()
fig.savefig(FIGS / "hubs_vs_puentes_50km.png", dpi=200)
print("Figura guardada")
