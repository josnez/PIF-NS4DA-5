"""
T11: modelos nulos para la red general (50 km).

1) Estructura (small-world): se compara clustering y camino promedio de la componente gigante
   contra (a) Erdos-Renyi con los mismos nodos y aristas y (b) modelo de configuracion
   (recableado que conserva el grado de cada nodo). sigma = (C/C_nulo) / (L/L_nulo).
2) Temporal: se mantienen los pares a < 50 km y se desordena cuando esta activo cada municipio.
   (a) permutacion de meses: conserva cuantos meses activos tiene cada municipio.
   (b) permutacion de anios: conserva ademas el mes calendario (la estacionalidad); solo
       cambia de que anio viene cada bloque. Si la red observada tiene mas aristas fuertes
       que (b), la co-ocurrencia no se explica solo por la temporada seca.

Entradas: resultados/red_general_50km.graphml, tabla_municipio_mes.csv, pares_candidatos_50km.csv
Salidas : resultados/nulo_estructura_50km.csv, resultados/nulo_temporal_50km.csv,
          figs/modelos_nulos_50km.png
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
REPS_ESTRUCTURA = 20
REPS_TEMPORAL = 200
W_FUERTE = 5
rng = np.random.default_rng(2026)

# ---------------------------------------------------------------- 1) estructura
G = nx.read_graphml(RES / "red_general_50km.graphml")
G = G.subgraph(max(nx.connected_components(G), key=len)).copy()
n, m = G.number_of_nodes(), G.number_of_edges()


def c_y_l(H):
    H = H.subgraph(max(nx.connected_components(H), key=len))
    return nx.average_clustering(H), nx.average_shortest_path_length(H)


C_obs, L_obs = c_y_l(G)
filas = [{"modelo": "Observada", "rep": 0, "clustering": C_obs, "camino_promedio": L_obs}]
for r in range(REPS_ESTRUCTURA):
    er = nx.gnm_random_graph(n, m, seed=int(rng.integers(1e9)))
    filas.append({"modelo": "Erdos-Renyi", "rep": r, **dict(zip(["clustering", "camino_promedio"], c_y_l(er)))})
    cf = nx.Graph(G)
    nx.double_edge_swap(cf, nswap=5 * m, max_tries=100 * m, seed=int(rng.integers(1e9)))
    filas.append({"modelo": "Configuracion", "rep": r, **dict(zip(["clustering", "camino_promedio"], c_y_l(cf)))})
    print(f"estructura rep {r + 1}/{REPS_ESTRUCTURA}")

e = pd.DataFrame(filas)
est = e.groupby("modelo")[["clustering", "camino_promedio"]].agg(["mean", "std"])
est.columns = ["clustering", "clustering_sd", "camino", "camino_sd"]
for mod in ["Erdos-Renyi", "Configuracion"]:
    est.loc[mod, "sigma"] = (C_obs / est.loc[mod, "clustering"]) / (L_obs / est.loc[mod, "camino"])
est = est.reindex(["Observada", "Erdos-Renyi", "Configuracion"]).round(4)
est.to_csv(RES / "nulo_estructura_50km.csv")
print(est.to_string())

# ---------------------------------------------------------------- 2) temporal
tabla = pd.read_csv(RES / "tabla_municipio_mes.csv", dtype={"cod": str})
tabla = tabla[tabla["anio"].between(2002, 2024)]
pares = pd.read_csv(RES / "pares_candidatos_50km.csv", dtype={"cod_a": str, "cod_b": str})

nodos = np.sort(tabla["cod"].unique())
fila = {c: i for i, c in enumerate(nodos)}
anios = np.arange(2002, 2025)
M = np.zeros((len(nodos), len(anios), 12), dtype=bool)          # municipio x anio x mes
M[tabla["cod"].map(fila), tabla["anio"] - 2002, tabla["mes"] - 1] = True
pares = pares[pares["cod_a"].isin(fila) & pares["cod_b"].isin(fila)]
ia, ib = pares["cod_a"].map(fila).to_numpy(), pares["cod_b"].map(fila).to_numpy()


def medir(X):
    Xf = X.reshape(len(nodos), -1)
    w = (Xf[ia] & Xf[ib]).sum(axis=1)
    return {"aristas_w1": int((w >= 1).sum()), f"aristas_w{W_FUERTE}": int((w >= W_FUERTE).sum()),
            "w_medio": w[w >= 1].mean(), "suma_w": int(w.sum())}


obs = medir(M)
res = [{"escenario": "Observada", "rep": 0, **obs}]
for r in range(REPS_TEMPORAL):
    Xm = M.reshape(len(nodos), -1).copy()
    for i in range(len(nodos)):
        Xm[i] = Xm[i, rng.permutation(Xm.shape[1])]
    res.append({"escenario": "Permutacion de meses", "rep": r, **medir(Xm.reshape(M.shape))})
    Xa = M[np.arange(len(nodos))[:, None], np.argsort(rng.random((len(nodos), len(anios))), axis=1)]
    res.append({"escenario": "Permutacion de anios", "rep": r, **medir(Xa)})
    if (r + 1) % 50 == 0:
        print(f"temporal rep {r + 1}/{REPS_TEMPORAL}")

t = pd.DataFrame(res)
cols = ["aristas_w1", f"aristas_w{W_FUERTE}", "w_medio", "suma_w"]
tem = t.groupby("escenario")[cols].agg(["mean", lambda s: s.quantile(0.05), lambda s: s.quantile(0.95)])
tem.columns = [f"{c}_{s}" for c in cols for s in ("media", "p05", "p95")]
tem = tem.reindex(["Observada", "Permutacion de anios", "Permutacion de meses"]).round(3)
tem.to_csv(RES / "nulo_temporal_50km.csv")
print(tem[[f"aristas_w{W_FUERTE}_media", f"aristas_w{W_FUERTE}_p95", "suma_w_media", "suma_w_p95"]].to_string())

# ---------------------------------------------------------------- figura
fig, axs = plt.subplots(1, 3, figsize=(13, 4))
for ax, var, tit in [(axs[0], "clustering", "Clustering medio"), (axs[1], "camino_promedio", "Camino promedio")]:
    for k, mod in enumerate(["Erdos-Renyi", "Configuracion"]):
        v = e.loc[e.modelo == mod, var]
        ax.scatter(np.full(len(v), k) + rng.normal(0, 0.05, len(v)), v, s=12, color="#7f8c8d", alpha=0.7)
    ax.axhline(e.loc[e.modelo == "Observada", var].iloc[0], color="#c0392b", lw=2, label="Observada")
    ax.set_xticks([0, 1], ["Erdős–Rényi", "Configuración"]); ax.set_title(tit); ax.legend(fontsize=8)
col = f"aristas_w{W_FUERTE}"
for esc, c in [("Permutacion de meses", "#bdc3c7"), ("Permutacion de anios", "#5d6d7e")]:
    axs[2].hist(t.loc[t.escenario == esc, col], bins=25, color=c, label=esc.replace("Permutacion", "Permutación").replace("anios", "años"))
axs[2].axvline(obs[col], color="#c0392b", lw=2, label="Observada")
axs[2].set_title(f"Aristas con ≥ {W_FUERTE} meses en común"); axs[2].set_ylabel("Réplicas"); axs[2].legend(fontsize=8)
fig.tight_layout()
fig.savefig(FIGS / "modelos_nulos_50km.png", dpi=200)
print("Figura guardada")
