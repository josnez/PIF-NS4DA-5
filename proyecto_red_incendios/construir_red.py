"""
T07: red general de co-ocurrencia mensual de incendios entre municipios.

Definicion (decisiones D1-D5, editables abajo):
  Nodo   : municipio (codigo DANE) con >= 1 mes activo en la tabla municipio-mes.
  Arista : par de municipios con centroides a menos de R km Y activos el mismo mes
           al menos MIN_W veces. No dirigida.
  Pesos  : w_meses   = numero de meses en que ambos estan activos (lo pide el plan)
           w_jaccard = w_meses / meses en que al menos uno esta activo (normalizado
                       por frecuencia; evita que dos municipios muy activos parezcan
                       "conectados" solo por ser frecuentes)

Entradas (resultados/): tabla_municipio_mes.csv, pares_candidatos_<R>km.csv,
                        centroides_municipios_dane2025.csv
Salidas  (resultados/): aristas_general_<R>km.csv para cada R, y red_general_50km.graphml
Requiere: pip install networkx
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"
RADIOS_KM = (25, 50, 75)
RADIO_PRINCIPAL = 50
MIN_W = 1                      # minimo de meses en comun para crear la arista

tabla = pd.read_csv(RES / "tabla_municipio_mes.csv", dtype={"cod": str})
cent = pd.read_csv(RES / "centroides_municipios_dane2025.csv", dtype={"cod": str})

# Matriz binaria municipio x mes (True = activo)
nodos = np.sort(tabla["cod"].unique())
periodos = np.sort(tabla["periodo"].unique())
fila = {c: i for i, c in enumerate(nodos)}
col = {p: j for j, p in enumerate(periodos)}
M = np.zeros((len(nodos), len(periodos)), dtype=bool)
M[tabla["cod"].map(fila).to_numpy(), tabla["periodo"].map(col).to_numpy()] = True
meses_activos = M.sum(axis=1)
print(f"Nodos con actividad: {len(nodos)} | meses con actividad: {len(periodos)}")


def aristas_para_radio(r):
    p = pd.read_csv(RES / f"pares_candidatos_{r}km.csv", dtype={"cod_a": str, "cod_b": str})
    p = p[p["cod_a"].isin(fila) & p["cod_b"].isin(fila)].copy()      # solo nodos activos
    ia, ib = p["cod_a"].map(fila).to_numpy(), p["cod_b"].map(fila).to_numpy()
    w = (M[ia] & M[ib]).sum(axis=1)
    union = meses_activos[ia] + meses_activos[ib] - w
    p["w_meses"] = w
    p["w_jaccard"] = np.where(union > 0, w / union, 0.0).round(5)
    return len(p), p[p["w_meses"] >= MIN_W].reset_index(drop=True)


for r in RADIOS_KM:
    n_cand, a = aristas_para_radio(r)
    a.to_csv(RES / f"aristas_general_{r}km.csv", index=False)
    G = nx.Graph()
    G.add_nodes_from(nodos)
    G.add_weighted_edges_from(a[["cod_a", "cod_b", "w_meses"]].itertuples(index=False, name=None))
    comp = sorted((len(c) for c in nx.connected_components(G)), reverse=True)
    grados = np.array([d for _, d in G.degree()])
    print(f"\n=== Umbral {r} km ===")
    print(f"  Pares candidatos entre nodos activos: {n_cand} | aristas con >= {MIN_W} mes en comun: {G.number_of_edges()}")
    print(f"  Densidad: {nx.density(G):.4f} | grado medio: {grados.mean():.1f} | grado maximo: {grados.max()}")
    print(f"  Nodos aislados: {int((grados == 0).sum())} | componentes: {len(comp)} | componente gigante: {comp[0]} ({comp[0] / len(nodos):.1%})")
    print(f"  w_meses: mediana {a['w_meses'].median():.0f}, p90 {a['w_meses'].quantile(.9):.0f}, max {a['w_meses'].max()} | aristas con w=1: {(a['w_meses'] == 1).mean():.1%}")

    if r == RADIO_PRINCIPAL:
        info = cent.set_index("cod")
        for c in nodos:
            G.nodes[c]["dpto"] = str(info.at[c, "dpto"])
            G.nodes[c]["mpio"] = str(info.at[c, "mpio"])
            G.nodes[c]["lon"] = float(info.at[c, "lon"])
            G.nodes[c]["lat"] = float(info.at[c, "lat"])
            G.nodes[c]["meses_activos"] = int(meses_activos[fila[c]])
        # w_jaccard por arista (indexado, sin busquedas lentas)
        jac = {(x, y): j for x, y, j in a[["cod_a", "cod_b", "w_jaccard"]].itertuples(index=False, name=None)}
        for u, v, d in G.edges(data=True):
            d["w_jaccard"] = jac.get((u, v), jac.get((v, u), 0.0))
        nx.write_graphml(G, RES / "red_general_50km.graphml")
        print("  Guardado: red_general_50km.graphml")

print("\nGuardados: aristas_general_25km.csv, _50km.csv, _75km.csv")