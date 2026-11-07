"""
T16: comparacion El Nino vs. La Nina con prueba de permutacion de las etiquetas de fase de los meses.

Pregunta: ¿la red de co-ocurrencia de El Nino es mas conectada que la de La Nina, mas de lo que
se esperaria si la fase de cada mes fuera arbitraria?

Definicion de red: la misma de construir_redes_fase.py (T08). Arista entre dos municipios a menos
de 50 km si estan activos el mismo mes al menos una vez dentro de la fase. Nodos: los mismos
municipios en todas las redes.

Estadistico: diferencia El Nino - La Nina en cada metrica. Se recalcula despues de barajar las
etiquetas de fase entre los meses (cada fase conserva su numero de meses). Tres versiones de la
permutacion, de menos a mas exigente:
  libre        : cualquier mes puede recibir cualquier etiqueta.
  mes_calendario: se baraja solo entre meses del mismo mes calendario (enero con enero...).
                  Controla la estacionalidad: El Nino y la temporada seca coinciden en dic-mar.
  anio         : se baraja solo entre meses del mismo anio. Controla que el reporte de IDEAM
                  crece mucho con los anios (2024 tiene ~9 veces los registros de 2002) y que
                  los meses de El Nino se concentran en anios de reporte alto (2015, 2019, 2023-24).
                  Es la version mas conservadora: tambien quita parte de la senal interanual de ENSO.
p-valor unilateral (H1: El Nino mas conectado) = (n.º de permutaciones con dif >= observada + 1) / (N + 1).
Para "componentes" H1 va al reves (menos componentes = mas conectada) y se cuenta dif <= observada.

Sensibilidad: se repite todo excluyendo 2023-2024 (reporte atipicamente alto, ver diagnostico_2023_24.py).

Entradas (../proyecto_red_incendios/resultados/): tabla_municipio_mes_fase.csv, meses_fase.csv,
                                                    pares_candidatos_50km.csv
Salidas: resultados/metricas_por_fase_50km.csv, resultados/permutacion_enso_50km.csv,
         figs/permutacion_enso_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.sparse import coo_matrix, csr_matrix
from scipy.sparse.csgraph import connected_components

BASE = Path(__file__).resolve().parent
RES_A = BASE.parent / "proyecto_red_incendios" / "resultados"
RES = BASE / "resultados"
FIGS = BASE / "figs"
RES.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)

RADIO_KM = 50
MIN_W = 1
N_PERM = 1000
SEMILLA = 42
FASES = ["El Nino", "La Nina", "Neutral"]
METRICAS = ["celdas", "activos_por_mes", "aristas", "grado_medio", "gigante_pct", "componentes",
            "clustering_medio", "aristas_por_celda"]
NOMBRES = {"celdas": "Municipio-mes activos", "activos_por_mes": "Municipios activos por mes",
           "aristas": "Aristas", "grado_medio": "Grado medio",
           "gigante_pct": "Componente gigante (%)", "componentes": "Componentes (≥2 nodos)",
           "clustering_medio": "Clustering medio", "aristas_por_celda": "Aristas por municipio-mes"}
# Sentido de H1 ("El Nino mas conectado"): +1 si se espera dif > 0, -1 si se espera dif < 0
SENTIDO = {m: 1 for m in METRICAS} | {"componentes": -1}


def cargar(anios_excluidos=()):
    """Matriz booleana municipio x mes (solo meses con reporte), igual que en T08."""
    tabla = pd.read_csv(RES_A / "tabla_municipio_mes_fase.csv", dtype={"cod": str})
    meses = pd.read_csv(RES_A / "meses_fase.csv")
    pares = pd.read_csv(RES_A / f"pares_candidatos_{RADIO_KM}km.csv", dtype={"cod_a": str, "cod_b": str})
    nodos = np.sort(tabla["cod"].unique())          # nodos de la red completa, antes de excluir anios
    if anios_excluidos:
        tabla = tabla[~tabla["anio"].isin(anios_excluidos)]
        meses = meses[~meses["anio"].isin(anios_excluidos)]
    fila = {c: i for i, c in enumerate(nodos)}
    pares = pares[pares["cod_a"].isin(fila) & pares["cod_b"].isin(fila)]
    ia, ib = pares["cod_a"].map(fila).to_numpy(), pares["cod_b"].map(fila).to_numpy()
    con_reporte = meses[meses["municipios_activos"] > 0].sort_values("periodo").reset_index(drop=True)
    col = {p: j for j, p in enumerate(con_reporte["periodo"])}
    M = np.zeros((len(nodos), len(con_reporte)), dtype=bool)
    M[tabla["cod"].map(fila).to_numpy(), tabla["periodo"].map(col).to_numpy()] = True
    return M, ia, ib, con_reporte


def metricas(M, ia, ib, cols):
    """Metricas de la red construida con los meses `cols`."""
    Mf = M[:, cols]
    w = (Mf[ia] & Mf[ib]).sum(axis=1)
    keep = w >= MIN_W
    a, b = ia[keep], ib[keep]
    n = M.shape[0]
    A = coo_matrix((np.ones(2 * len(a)), (np.r_[a, b], np.r_[b, a])), shape=(n, n)).tocsr()
    k = np.asarray(A.sum(axis=1)).ravel()
    _, lab = connected_components(A, directed=False)
    tam = np.bincount(lab)
    # Clustering local: triangulos / pares de vecinos. Promedio sobre nodos con al menos un vecino
    # (los de grado 1 cuentan como 0), igual que nx.average_clustering sobre la red sin aislados.
    tri = np.asarray(csr_matrix(A @ A).multiply(A).sum(axis=1)).ravel() / 2
    c = np.divide(2 * tri, k * (k - 1), out=np.zeros(n), where=k > 1)
    celdas = int(Mf.sum())
    return {"celdas": celdas, "activos_por_mes": celdas / len(cols),
            "aristas": int(keep.sum()), "grado_medio": k.mean(),
            "gigante_pct": 100 * tam.max() / n, "componentes": int((tam >= 2).sum()),
            "clustering_medio": c[k > 0].mean() if (k > 0).any() else 0.0,
            "aristas_por_celda": keep.sum() / celdas if celdas else 0.0}


def diferencia(M, ia, ib, fase_mes):
    mn = metricas(M, ia, ib, np.where(fase_mes == "El Nino")[0])
    ml = metricas(M, ia, ib, np.where(fase_mes == "La Nina")[0])
    return {m: mn[m] - ml[m] for m in METRICAS}


def barajar(fase_mes, estratos, rng):
    """Permuta las etiquetas dentro de cada estrato (un solo estrato = permutacion libre)."""
    nueva = fase_mes.copy()
    for e in np.unique(estratos):
        idx = np.where(estratos == e)[0]
        nueva[idx] = rng.permutation(fase_mes[idx])
    return nueva


def correr(anios_excluidos=(), etiqueta="todos los anios"):
    M, ia, ib, meses = cargar(anios_excluidos)
    fase_mes = meses["fase"].to_numpy()
    obs = {f: metricas(M, ia, ib, np.where(fase_mes == f)[0]) for f in FASES}
    tabla = pd.DataFrame(obs).T.reset_index(names="fase")
    tabla.insert(1, "meses", [int((fase_mes == f).sum()) for f in FASES])
    tabla.insert(0, "periodo", etiqueta)
    d_obs = {m: obs["El Nino"][m] - obs["La Nina"][m] for m in METRICAS}

    estratos = {"libre": np.zeros(len(meses), dtype=int),
                "mes_calendario": meses["mes"].to_numpy(),
                "anio": meses["anio"].to_numpy()}
    filas, nulos = [], {}
    for nombre, est in estratos.items():
        rng = np.random.default_rng(SEMILLA)
        sims = pd.DataFrame([diferencia(M, ia, ib, barajar(fase_mes, est, rng)) for _ in range(N_PERM)])
        nulos[nombre] = sims
        for m in METRICAS:
            filas.append({"periodo": etiqueta, "permutacion": nombre, "metrica": m,
                          "dif_observada": d_obs[m], "nulo_media": sims[m].mean(),
                          "nulo_p05": sims[m].quantile(.05), "nulo_p95": sims[m].quantile(.95),
                          "p_unilateral": ((SENTIDO[m] * sims[m] >= SENTIDO[m] * d_obs[m]).sum() + 1)
                                          / (N_PERM + 1)})
        print(f"  [{etiqueta}] permutacion {nombre}: lista")
    return tabla, pd.DataFrame(filas), d_obs, nulos


print("Corriendo con todos los anios...")
t1, p1, d_obs, nulos = correr()
print("Corriendo sin 2023-2024...")
t2, p2, _, _ = correr((2023, 2024), "sin 2023-2024")
pd.concat([t1, t2]).to_csv(RES / "metricas_por_fase_50km.csv", index=False)
perm = pd.concat([p1, p2])
perm.to_csv(RES / "permutacion_enso_50km.csv", index=False)

pd.set_option("display.width", 200)
print("\nMETRICAS POR FASE")
print(pd.concat([t1, t2]).round(3).to_string(index=False))
print("\nPRUEBA DE PERMUTACION (dif = El Nino - La Nina; p unilateral, H1: El Nino mas conectado)")
print(perm.pivot_table(index=["periodo", "metrica"], columns="permutacion", values="p_unilateral")
      .round(4).to_string())

# --- Figura: distribucion nula de la diferencia y valor observado (todos los anios) ------
mostrar = ["aristas", "grado_medio", "gigante_pct", "clustering_medio"]
colores = {"libre": "#9aa5b1", "mes_calendario": "#4c78a8", "anio": "#f58518"}
etiquetas = {"libre": "Libre", "mes_calendario": "Por mes calendario", "anio": "Por año"}
fig, axes = plt.subplots(1, len(mostrar), figsize=(18, 4.6))
for ax, m in zip(axes, mostrar):
    for nombre, sims in nulos.items():
        ax.hist(sims[m], bins=35, alpha=.55, color=colores[nombre], label=f"Nulo: {etiquetas[nombre].lower()}")
    ax.axvline(d_obs[m], color="#d62728", lw=2.2, label="Diferencia observada")
    ax.axvline(0, color="black", lw=.8, ls=":")
    p_max = p1.query("metrica == @m")["p_unilateral"].max()
    ax.text(.02, .96, f"p ≤ {p_max:.3f}\nen las tres versiones", transform=ax.transAxes,
            va="top", fontsize=9, bbox=dict(facecolor="white", edgecolor="none", alpha=.8))
    ax.set_title(NOMBRES[m], fontsize=11)
    ax.set_xlabel("Diferencia El Niño − La Niña")
axes[0].set_ylabel("Permutaciones")
manejadores, textos = axes[0].get_legend_handles_labels()
fig.legend(manejadores, textos, loc="lower center", ncol=4, frameon=False, fontsize=10)
fig.suptitle(f"Prueba de permutación de las etiquetas de fase ({N_PERM} permutaciones por versión, red a {RADIO_KM} km)",
             fontsize=12)
fig.tight_layout(rect=(0, .07, 1, 1))
fig.savefig(FIGS / "permutacion_enso_50km.png", dpi=150)
print("\nGuardados: resultados/metricas_por_fase_50km.csv, resultados/permutacion_enso_50km.csv, "
      "figs/permutacion_enso_50km.png")
