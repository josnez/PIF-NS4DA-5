"""
T15: difusion SIR sobre la red de co-ocurrencia e inmunizacion de hubs vs. puentes.

Idea: tratar la activacion de incendios como algo que "se contagia" entre municipios vecinos de la
red. Un municipio activo (I) puede activar a sus vecinos susceptibles (S) y luego deja de estar
activo (R). Con esto se pregunta desde donde se propaga mas el riesgo y si conviene mas proteger
("vacunar") a los hubs o a los puentes.

1. Calibracion de parametros con los datos (paso de tiempo = 1 mes)
   gamma : probabilidad mensual de dejar de estar activo = 1 - P(activo en t+1 | activo en t).
           1 / gamma es la duracion media de un episodio de actividad.
   beta  : probabilidad mensual de que un vecino activo active a un municipio inactivo. Se estima
           por maxima verosimilitud con el modelo
               P(activo en t+1 | inactivo en t, k vecinos activos en t) = 1 - (1 - p0)(1 - beta)^k,
           donde p0 es la activacion "espontanea" (sin vecinos activos).
   Se calibra con todos los meses y por separado con los meses de El Nino y de La Nina.
   Se compara la transmisibilidad por arista T = beta / (1 - (1 - beta)(1 - gamma)) con el umbral
   epidemico de la red T_c = <k> / (<k^2> - <k>) (Newman 2002; Pastor-Satorras et al. 2015).
   Ojo: beta mezcla contagio con causas comunes (clima de la region), asi que es una cota superior
   del contagio real. El modelo SIR no incluye p0 (no hay activaciones espontaneas durante la
   simulacion): mide solo el efecto de la estructura de la red.

2. Escenarios: SIR sobre la red general con los parametros de cada fase. Se siembra un municipio
   al azar y se mide el tamano final del brote (fraccion de municipios que llegaron a estar activos).

3. Potencial propagador: para cada municipio como semilla, tamano final medio del brote.

4. Inmunizacion: se "vacunan" (quitan) los k municipios con mayor grado (hubs), con mayor
   intermediacion (puentes) o al azar, con los rankings de B (T13), y se mide el brote medio.
   Ademas del escenario general y el de El Nino se corre uno hipotetico con beta x 2 (El Nino mas
   intenso), para ver si la estrategia que conviene cambia cuando los brotes se vuelven grandes.

Entradas: ../proyecto_red_incendios/resultados/red_general_50km.graphml, tabla_municipio_mes_fase.csv,
          meses_fase.csv, ../paquete_B/resultados/centralidad_general_50km.csv
Salidas : resultados/sir_parametros_50km.csv, resultados/sir_escenarios_50km.csv,
          resultados/sir_propagadores_50km.csv, resultados/sir_inmunizacion_50km.csv,
          figs/sir_inmunizacion_50km.png, figs/mapa_propagadores_50km.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import spearmanr

BASE = Path(__file__).resolve().parent
A_DIR = BASE.parent / "proyecto_red_incendios"
RES_A = A_DIR / "resultados"
RES_B = BASE.parent / "paquete_B" / "resultados"
RES, FIGS = BASE / "resultados", BASE / "figs"
RES.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)
RADIO_KM = 50
SEMILLA = 42
N_SIM = 2000                 # brotes por escenario
N_REP_SEMILLA = 50           # brotes por municipio semilla (potencial propagador)
K_VACUNA = [15, 25, 50, 100]
N_AZAR = 20                  # conjuntos aleatorios de vacunados por k
UMBRAL_BROTE = 0.05          # brote "grande" = llega a mas del 5 % de los municipios
K_MAX_CALIB = 15             # en la calibracion, k >= 15 vecinos activos se agrupan
rng = np.random.default_rng(SEMILLA)

# --- Red y datos -----------------------------------------------------------------------------
G = nx.read_graphml(RES_A / f"red_general_{RADIO_KM}km.graphml")
nodos = sorted(G.nodes())
fila = {c: i for i, c in enumerate(nodos)}
N = len(nodos)
Adj = nx.to_scipy_sparse_array(G, nodelist=nodos, weight=None, format="csr").astype(np.int32)
k = np.asarray(Adj.sum(axis=1)).ravel()
T_c = k.mean() / ((k ** 2).mean() - k.mean())

tabla = pd.read_csv(RES_A / "tabla_municipio_mes_fase.csv", dtype={"cod": str})
meses = pd.read_csv(RES_A / "meses_fase.csv")
meses = meses[meses["municipios_activos"] > 0].sort_values("periodo").reset_index(drop=True)
col = {p: j for j, p in enumerate(meses["periodo"])}
tabla = tabla[tabla["cod"].isin(fila)]
M = np.zeros((N, len(meses)), dtype=bool)
M[tabla["cod"].map(fila).to_numpy(), tabla["periodo"].map(col).to_numpy()] = True
per = pd.PeriodIndex(meses["periodo"], freq="M")
consecutivo = np.r_[[(per[j + 1] - per[j]).n == 1 for j in range(len(per) - 1)]]   # t -> t+1 sin hueco


# --- 1. Calibracion ---------------------------------------------------------------------------
def calibrar(fases):
    """gamma y beta (MLE) con las transiciones t -> t+1 en que el mes t es de alguna de `fases`."""
    t_ok = np.where(consecutivo & meses["fase"].iloc[:-1].isin(fases).to_numpy())[0]
    a, b = M[:, t_ok], M[:, t_ok + 1]
    gamma = 1 - (a & b).sum() / a.sum()
    vec_act = np.minimum(Adj @ a.astype(np.int32), K_MAX_CALIB)
    sus = ~a
    kk = vec_act[sus]
    nuevos = b[sus]
    n_k = np.bincount(kk, minlength=K_MAX_CALIB + 1)
    y_k = np.bincount(kk, weights=nuevos, minlength=K_MAX_CALIB + 1)
    p0 = y_k[0] / n_k[0]
    kv = np.arange(K_MAX_CALIB + 1)
    betas = np.linspace(0.001, 0.15, 1500)
    ll = [np.sum(y_k * np.log(1 - (1 - p0) * (1 - bt) ** kv) + (n_k - y_k) * np.log((1 - p0) * (1 - bt) ** kv))
          for bt in betas]
    beta = betas[int(np.argmax(ll))]
    T = beta / (1 - (1 - beta) * (1 - gamma))
    return {"meses_transicion": len(t_ok), "gamma": gamma, "duracion_media_meses": 1 / gamma,
            "p0_espontanea": p0, "beta": beta, "P_act_1_vecino": y_k[1] / n_k[1],
            "T_arista": T, "T_c_red": T_c, "T_sobre_Tc": T / T_c}


ESCENARIOS = [("General", ["El Nino", "La Nina", "Neutral"]), ("El Niño", ["El Nino"]), ("La Niña", ["La Nina"])]
par = pd.DataFrame([{"escenario": e, **calibrar(f)} for e, f in ESCENARIOS])
par.to_csv(RES / "sir_parametros_50km.csv", index=False)
pd.set_option("display.width", 200)
print("1) PARAMETROS CALIBRADOS (paso = 1 mes)")
print(par.round(4).to_string(index=False))


# --- SIR vectorizado: R brotes en paralelo ---------------------------------------------------
def sir(semillas, beta, gamma, vacunados=None, rng=rng):
    """Corre un brote por semilla (en paralelo). Devuelve la fraccion de municipios que llego a I."""
    R_ = len(semillas)
    I = np.zeros((N, R_), dtype=bool)
    I[semillas, np.arange(R_)] = True
    Rec = np.zeros_like(I)
    if vacunados is not None:
        Rec[vacunados, :] = True
    alguna = I.copy()
    while I.any():
        n_inf = Adj @ I.astype(np.int32)
        p = 1 - (1 - beta) ** n_inf
        nuevos = (~I) & (~Rec) & (rng.random(I.shape) < p)
        recupera = I & (rng.random(I.shape) < gamma)
        Rec |= recupera
        I = (I & ~recupera) | nuevos
        alguna |= nuevos
    return alguna.sum(axis=0) / N


# --- 2. Escenarios ------------------------------------------------------------------------------
filas, tamanos = [], {}
for r in par.itertuples():
    t = sir(rng.integers(N, size=N_SIM), r.beta, r.gamma)
    tamanos[r.escenario] = t
    filas.append({"escenario": r.escenario, "beta": r.beta, "gamma": r.gamma, "T_sobre_Tc": r.T_sobre_Tc,
                  "brote_medio_pct": 100 * t.mean(), "brote_p95_pct": 100 * np.quantile(t, .95),
                  "P_brote_grande": (t > UMBRAL_BROTE).mean(),
                  "brote_medio_si_grande_pct": 100 * t[t > UMBRAL_BROTE].mean() if (t > UMBRAL_BROTE).any() else 0})
esc = pd.DataFrame(filas)
esc.to_csv(RES / "sir_escenarios_50km.csv", index=False)
print(f"\n2) ESCENARIOS ({N_SIM} brotes, una semilla al azar; brote grande = > {UMBRAL_BROTE:.0%} de los municipios)")
print(esc.round(4).to_string(index=False))

# --- 3. Potencial propagador (parametros de El Nino) ---------------------------------------
p_nino = par.set_index("escenario").loc["El Niño"]
acum = np.zeros(N)
for _ in range(N_REP_SEMILLA):
    acum += sir(np.arange(N), p_nino.beta, p_nino.gamma)
cent = pd.read_csv(RES_B / "centralidad_general_50km.csv", dtype={"cod": str}).set_index("cod")
prop = pd.DataFrame({"cod": nodos, "brote_medio_pct": 100 * acum / N_REP_SEMILLA, "grado_red": k})
prop = prop.join(cent[["mpio", "dpto", "lon", "lat", "intermediacion", "comunidad", "hub", "puente"]], on="cod")
prop = prop.sort_values("brote_medio_pct", ascending=False)
prop.round(4).to_csv(RES / "sir_propagadores_50km.csv", index=False)
ok = prop.dropna(subset=["intermediacion"])
rho_k = spearmanr(ok["grado_red"], ok["brote_medio_pct"])[0]
rho_b = spearmanr(ok["intermediacion"], ok["brote_medio_pct"])[0]
print(f"\n3) POTENCIAL PROPAGADOR (parametros El Nino, {N_REP_SEMILLA} brotes por semilla)")
print(f"   Spearman con grado = {rho_k:.2f}; con intermediacion = {rho_b:.2f}")
print(prop.head(15)[["mpio", "dpto", "brote_medio_pct", "grado_red", "intermediacion", "hub", "puente"]]
      .round(3).to_string(index=False))

# --- 4. Inmunizacion -------------------------------------------------------------------------
orden_hubs = [fila[c] for c in cent.sort_values("grado", ascending=False).index if c in fila]
orden_puentes = [fila[c] for c in cent.sort_values("intermediacion", ascending=False).index if c in fila]
ESTRES = "El Niño, β×2 (hipotético)"
p_estres = par.set_index("escenario").loc["El Niño"].copy()
p_estres["beta"] *= 2
tamanos[ESTRES] = sir(rng.integers(N, size=N_SIM), p_estres.beta, p_estres.gamma)
T_estres = p_estres.beta / (1 - (1 - p_estres.beta) * (1 - p_estres.gamma))
print(f"\n   Escenario {ESTRES}: T/T_c = {T_estres / T_c:.2f}, brote medio = {100 * tamanos[ESTRES].mean():.2f} %, "
      f"P(brote grande) = {(tamanos[ESTRES] > UMBRAL_BROTE).mean():.3f}")
esc_inm = [("General", *par.set_index("escenario").loc["General", ["beta", "gamma"]]),
           ("El Niño", *par.set_index("escenario").loc["El Niño", ["beta", "gamma"]]),
           (ESTRES, p_estres.beta, p_estres.gamma)]
filas = []
for r in (pd.DataFrame(esc_inm, columns=["escenario", "beta", "gamma"]).itertuples()):
    base = 100 * tamanos[r.escenario].mean()
    filas.append({"escenario": r.escenario, "estrategia": "sin vacunar", "k": 0, "brote_medio_pct": base,
                  "reduccion_pct": 0.0})
    for kv in K_VACUNA:
        conjuntos = {"hubs (grado)": [np.array(orden_hubs[:kv])],
                     "puentes (intermediacion)": [np.array(orden_puentes[:kv])],
                     "al azar": [rng.choice(N, kv, replace=False) for _ in range(N_AZAR)]}
        for est, lista in conjuntos.items():
            res_est = []
            for vac in lista:
                libres = np.setdiff1d(np.arange(N), vac)
                n_sim = N_SIM if len(lista) == 1 else N_SIM // N_AZAR * 2
                res_est.append(sir(rng.choice(libres, n_sim), r.beta, r.gamma, vac).mean())
            m = 100 * np.mean(res_est)
            filas.append({"escenario": r.escenario, "estrategia": est, "k": kv, "brote_medio_pct": m,
                          "reduccion_pct": 100 * (1 - m / base)})
inm = pd.DataFrame(filas)
inm.to_csv(RES / "sir_inmunizacion_50km.csv", index=False)
print("\n4) INMUNIZACION (brote medio en % de municipios; reduccion respecto a no vacunar)")
print(inm.pivot_table(index=["escenario", "k"], columns="estrategia", values="brote_medio_pct").round(2).to_string())

# --- Figura 1: escenarios e inmunizacion ------------------------------------------------------
colores_esc = {"General": "#7f7f7f", "El Niño": "#d1495b", "La Niña": "#2f6db5"}
colores_est = {"hubs (grado)": "#2f6db5", "puentes (intermediacion)": "#c0392b", "al azar": "#7f7f7f"}
fig, axes = plt.subplots(1, 4, figsize=(22, 4.8))
ax = axes[0]
bins = np.linspace(0, max(tamanos[e].max() for e in colores_esc) * 100, 40)
for e in colores_esc:
    t = tamanos[e]
    p = esc.set_index("escenario").loc[e]
    ax.hist(100 * t, bins=bins, alpha=.55, color=colores_esc[e],
            label=f"{e}: T/T_c = {p.T_sobre_Tc:.2f}, brote medio {p.brote_medio_pct:.1f} %")
ax.set_yscale("log")
ax.set_xlabel("Tamaño final del brote (% de municipios)")
ax.set_ylabel(f"Brotes (de {N_SIM}, escala log)")
ax.set_title("Brotes SIR con los parámetros de cada fase", fontsize=11)
ax.legend(fontsize=8, frameon=False)
for ax, e in zip(axes[1:], ["General", "El Niño", ESTRES]):
    d = inm[inm.escenario == e]
    base = d.query("k == 0")["brote_medio_pct"].iloc[0]
    for est, c in colores_est.items():
        s = d[d.estrategia == est]
        ax.plot(np.r_[0, s.k], np.r_[base, s.brote_medio_pct], "o-", color=c, lw=2, label=f"Vacunar {est}")
    ax.set_xlabel("Municipios vacunados (k)")
    ax.set_ylabel("Brote medio (% de municipios)")
    ax.set_title(f"Inmunización: {e}", fontsize=11)
    ax.set_ylim(bottom=0)
    ax.grid(alpha=.3)
    ax.legend(fontsize=8.5, frameon=False)
fig.suptitle(f"Difusión SIR en la red de co-ocurrencia (red general a {RADIO_KM} km; β y γ calibrados con los datos, paso = 1 mes)",
             fontsize=11.5)
fig.tight_layout()
fig.savefig(FIGS / "sir_inmunizacion_50km.png", dpi=150)
plt.close(fig)

# --- Figura 2: mapa del potencial propagador ---------------------------------------------------
shp = next(p for p in (A_DIR / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
dptos = gpd.read_file(shp)[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)
pos = {n: (d["lon"], d["lat"]) for n, d in G.nodes(data=True)}
p2 = prop.copy()
p2["x"] = [pos[c][0] for c in p2.cod]
p2["y"] = [pos[c][1] for c in p2.cod]
p2 = p2.sort_values("brote_medio_pct")
fig, ax = plt.subplots(figsize=(7.2, 8.4), dpi=200)
dptos.plot(ax=ax, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4)
sc = ax.scatter(p2.x, p2.y, s=6 + 0.9 * p2.brote_medio_pct ** 1.3, c=p2.brote_medio_pct, cmap="YlOrRd",
                edgecolors="#666", linewidths=0.2, zorder=3)
# Los mayores propagadores estan todos juntos en el altiplano: se listan en un recuadro en vez de rotularlos
top = prop.head(8)
lista = "\n".join(f"{i}. {str(r.mpio).title()} ({str(r.dpto).title()}): {r.brote_medio_pct:.1f} %"
                  for i, r in enumerate(top.itertuples(), start=1))
ax.text(0.02, 0.02, "Mayores propagadores\n" + lista, transform=ax.transAxes, fontsize=6.8, va="bottom",
        bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="#cccccc", alpha=0.9), zorder=5)
cb = fig.colorbar(sc, ax=ax, shrink=0.55, pad=0.01)
cb.set_label("Brote medio si el municipio es la semilla (% de municipios)", fontsize=8)
cb.ax.tick_params(labelsize=7)
ax.set_xlim(-79.6, -66.4); ax.set_ylim(-4.4, 13.6)
ax.set_aspect(1 / np.cos(np.radians(4.5)))
ax.set_xticks([]); ax.set_yticks([]); ax.set_xlabel(""); ax.set_ylabel("")
for s in ax.spines.values():
    s.set_visible(False)
ax.set_title(f"Potencial propagador de cada municipio (SIR con parámetros de El Niño,\n"
             f"{N_REP_SEMILLA} brotes por semilla)", fontsize=10)
fig.savefig(FIGS / "mapa_propagadores_50km.png", bbox_inches="tight")
print("\nGuardados: resultados/sir_*.csv, figs/sir_inmunizacion_50km.png, figs/mapa_propagadores_50km.png")
