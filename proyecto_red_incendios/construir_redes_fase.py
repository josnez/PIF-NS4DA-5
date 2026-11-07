"""
T08: una red por fase ENSO (El Nino, La Nina, Neutral) y comparacion con actividad igualada.

Misma definicion que construir_red.py, aplicada a los meses de cada fase:
  Nodos  : los MISMOS municipios en las tres redes (D4), para que sean comparables.
  Arista : par a menos de RADIO_KM km, activos el mismo mes al menos MIN_W veces dentro de la fase.
  Pesos  : w_meses  = meses de la fase en que coinciden
           w_prop   = w_meses / meses de la fase CON REPORTE (D6: los meses sin registros se
                      tratan como ausentes y no entran en el denominador)
           w_jaccard= w_meses / meses de la fase en que al menos uno esta activo

La red de El Nino tiene mas actividad que la de La Nina (mas municipios activos por mes y mas
meses). Para no confundir "mas actividad" con "mas conexion", se repite la comparacion
submuestreando meses de cada fase hasta igualar el numero de celdas municipio-mes de la fase
de referencia (La Nina), N_REP veces (parte B).

Entradas (resultados/): tabla_municipio_mes_fase.csv, meses_fase.csv,
                        pares_candidatos_<R>km.csv, centroides_municipios_dane2025.csv
Salidas  (resultados/): aristas_<fase>_<R>km.csv, red_<fase>_<R>km.graphml,
                        resumen_redes_fase_<R>km.csv, resumen_igualada_<R>km.csv
                        (con sufijo si se excluyen anios)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"
RADIO_KM = 50
MIN_W = 1
N_REP = 200
SEMILLA = 42
FASES = ["El Nino", "La Nina", "Neutral"]
REFERENCIA = "La Nina"
# Sensibilidad: anios a excluir (p. ej. (2023, 2024) por su reporte muy alto). () = sin exclusion.
# Si se excluyen anios, los archivos de salida llevan el sufijo _sin2023_24 y no pisan los principales.
ANIOS_EXCLUIDOS = ()
SUFIJO = "" if not ANIOS_EXCLUIDOS else "_sin" + "_".join(str(a)[-2:] if i else str(a) for i, a in enumerate(ANIOS_EXCLUIDOS))

tabla = pd.read_csv(RES / "tabla_municipio_mes_fase.csv", dtype={"cod": str})
meses = pd.read_csv(RES / "meses_fase.csv")
if ANIOS_EXCLUIDOS:
    tabla = tabla[~tabla["anio"].isin(ANIOS_EXCLUIDOS)].copy()
    meses = meses[~meses["anio"].isin(ANIOS_EXCLUIDOS)].copy()
    print("Anios excluidos:", ANIOS_EXCLUIDOS)
cent = pd.read_csv(RES / "centroides_municipios_dane2025.csv", dtype={"cod": str}).set_index("cod")
pares = pd.read_csv(RES / f"pares_candidatos_{RADIO_KM}km.csv", dtype={"cod_a": str, "cod_b": str})

nodos = np.sort(tabla["cod"].unique())
fila = {c: i for i, c in enumerate(nodos)}
pares = pares[pares["cod_a"].isin(fila) & pares["cod_b"].isin(fila)].reset_index(drop=True)
ia, ib = pares["cod_a"].map(fila).to_numpy(), pares["cod_b"].map(fila).to_numpy()

# Matriz municipio x mes sobre los meses CON reporte (municipios_activos > 0)
con_reporte = meses[meses["municipios_activos"] > 0].sort_values("periodo").reset_index(drop=True)
col = {p: j for j, p in enumerate(con_reporte["periodo"])}
M = np.zeros((len(nodos), len(con_reporte)), dtype=bool)
M[tabla["cod"].map(fila).to_numpy(), tabla["periodo"].map(col).to_numpy()] = True
fase_mes = con_reporte["fase"].to_numpy()
celdas_mes = M.sum(axis=0)                                   # municipios activos en cada mes


def metricas(cols):
    """Aristas con >= MIN_W meses en comun usando solo las columnas (meses) indicadas."""
    Mf = M[:, cols]
    w = (Mf[ia] & Mf[ib]).sum(axis=1)
    keep = w >= MIN_W
    a, b = ia[keep], ib[keep]
    n = len(nodos)
    A = coo_matrix((np.ones(len(a)), (a, b)), shape=(n, n))
    k = np.bincount(np.r_[a, b], minlength=n)
    _, lab = connected_components(A, directed=False)
    gig = np.bincount(lab).max()
    return {"meses": len(cols), "celdas": int(Mf.sum()), "aristas": int(keep.sum()),
            "aristas_w2": int((w >= 2).sum()), "densidad": keep.sum() / (n * (n - 1) / 2),
            "grado_medio": k.mean(), "aislados": int((k == 0).sum()),
            "gigante_pct": gig / n}, w, keep


# --- Parte A: una red por fase con todos sus meses -------------------------------------
filas = []
for f in FASES:
    cols = np.where(fase_mes == f)[0]
    m, w, keep = metricas(cols)
    n_den = len(cols)                                          # meses de la fase con reporte
    Mf = M[:, cols]
    n_a, n_b = Mf[ia].sum(axis=1), Mf[ib].sum(axis=1)
    union = n_a + n_b - w                                      # meses con al menos uno activo
    jac = np.divide(w, union, out=np.zeros(len(w)), where=union > 0)
    ar = pares.loc[keep, ["cod_a", "cod_b", "dist_km"]].copy()
    ar["w_meses"] = w[keep]
    ar["w_prop"] = (w[keep] / n_den).round(5)
    ar["w_jaccard"] = jac[keep].round(5)
    tag = f.replace(" ", "_")
    ar.to_csv(RES / f"aristas_{tag}_{RADIO_KM}km{SUFIJO}.csv", index=False)

    G = nx.Graph()
    for c in nodos:
        G.add_node(c, dpto=str(cent.at[c, "dpto"]), mpio=str(cent.at[c, "mpio"]),
                   lon=float(cent.at[c, "lon"]), lat=float(cent.at[c, "lat"]),
                   meses_activos_fase=int(Mf[fila[c]].sum()))
    for r in ar.itertuples(index=False):
        G.add_edge(r.cod_a, r.cod_b, weight=int(r.w_meses), w_prop=float(r.w_prop), w_jaccard=float(r.w_jaccard))
    nx.write_graphml(G, RES / f"red_{tag}_{RADIO_KM}km{SUFIJO}.graphml")
    filas.append({"fase": f, "meses_denominador": n_den, **m,
                  "w_prop_mediana": float(ar["w_prop"].median()) if len(ar) else 0.0})

res = pd.DataFrame(filas)
res.to_csv(RES / f"resumen_redes_fase_{RADIO_KM}km{SUFIJO}.csv", index=False)
print("A) REDES POR FASE (todos los meses de cada fase; NO comparar densidades sin leer la parte B)")
print(res.round(4).to_string(index=False))

# --- Parte B: actividad igualada ---------------------------------------------------------
objetivo = int(res.loc[res["fase"] == REFERENCIA, "celdas"].iloc[0])
rng = np.random.default_rng(SEMILLA)
filas = []
for f in FASES:
    cols_f = np.where(fase_mes == f)[0]
    if f == REFERENCIA:
        m, _, _ = metricas(cols_f)
        filas.append({"fase": f, "estadistico": "observado", **{k: m[k] for k in ("meses", "celdas", "aristas", "aristas_w2", "grado_medio", "aislados", "gigante_pct")}})
        continue
    sims = []
    for _ in range(N_REP):
        orden = rng.permutation(cols_f)
        acum = np.cumsum(celdas_mes[orden])
        # Si la fase tiene menos celdas que el objetivo, se usan todos sus meses (no se puede igualar)
        sel = orden[: int(np.searchsorted(acum, objetivo) + 1)]
        m, _, _ = metricas(sel)
        sims.append(m)
    s = pd.DataFrame(sims)
    for est, fn in (("media", s.mean()), ("desv", s.std()), ("p05", s.quantile(.05)), ("p95", s.quantile(.95))):
        filas.append({"fase": f, "estadistico": est, **{k: fn[k] for k in ("meses", "celdas", "aristas", "aristas_w2", "grado_medio", "aislados", "gigante_pct")}})
ig = pd.DataFrame(filas)
ig.to_csv(RES / f"resumen_igualada_{RADIO_KM}km{SUFIJO}.csv", index=False)
print(f"\nB) ACTIVIDAD IGUALADA a {objetivo} celdas municipio-mes (referencia: {REFERENCIA}); {N_REP} submuestras")
print(ig.round(3).to_string(index=False))
print("\nGuardados: aristas_<fase>, red_<fase>.graphml, resumen_redes_fase y resumen_igualada")