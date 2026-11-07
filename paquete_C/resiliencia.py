"""
T14: resiliencia de la red de co-ocurrencia ante la remocion de municipios.

Pregunta: ¿que tan rapido se fragmenta la red si se "quitan" municipios (por ejemplo, porque
se controla el fuego en ellos), y importa a cuales se quita primero?

Estrategias de remocion (se quita un municipio a la vez hasta quitarlos todos):
  aleatoria       : orden al azar, promedio de N_REP replicas.
  grado           : siempre el municipio con mas vecinos en la red que queda (adaptativa).
  intermediacion  : siempre el de mayor intermediacion en la red que queda (adaptativa, se
                    recalcula en cada paso).
Medida: S(f) = tamano de la componente gigante / N inicial, despues de quitar la fraccion f.
Resumen:
  AUC   = area bajo S(f) entre f = 0 y f = 1 (menor = la red se rompe mas rapido).
  f_50  = fraccion que hay que quitar para que la gigante baje a la mitad de su tamano inicial.
Se corre sobre la red general y sobre las redes de El Nino y La Nina (redes sin pesos; los
mismos 1.032 municipios en todas).

Entradas: ../proyecto_red_incendios/resultados/red_<general|El_Nino|La_Nina>_50km.graphml
Salidas : resultados/resiliencia_curvas_50km.csv, resultados/resiliencia_resumen_50km.csv,
          resultados/resiliencia_orden_remocion_50km.csv, figs/resiliencia_50km.png
Requiere: pip install igraph (la intermediacion adaptativa con networkx tarda demasiado)
"""
from pathlib import Path
import numpy as np
import pandas as pd
import networkx as nx
import igraph as ig
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
RES_A = BASE.parent / "proyecto_red_incendios" / "resultados"
RES, FIGS = BASE / "resultados", BASE / "figs"
RES.mkdir(exist_ok=True)
FIGS.mkdir(exist_ok=True)
RADIO_KM = 50
N_REP = 100
SEMILLA = 42
REDES = [("general", "Red general"), ("El_Nino", "El Niño"), ("La_Nina", "La Niña")]
ESTRATEGIAS = [("aleatoria", "Aleatoria"), ("grado", "Por grado (hubs)"),
               ("intermediacion", "Por intermediación (puentes)")]


def cargar(nombre):
    G = nx.read_graphml(RES_A / f"red_{nombre}_{RADIO_KM}km.graphml")
    nodos = list(G.nodes())
    idx = {c: i for i, c in enumerate(nodos)}
    g = ig.Graph(n=len(nodos), edges=[(idx[u], idx[v]) for u, v in G.edges()])
    g.vs["cod"] = nodos
    g.vs["mpio"] = [G.nodes[c]["mpio"] for c in nodos]
    g.vs["dpto"] = [G.nodes[c]["dpto"] for c in nodos]
    return g


def gigante(g):
    return max(g.connected_components().sizes()) if g.vcount() else 0


def remover(g, estrategia, rng=None):
    """Devuelve S(f) para f = 0, 1/N, ..., 1 y el orden de remocion (codigos)."""
    h = g.copy()
    n = g.vcount()
    S, orden = [gigante(h) / n], []
    while h.vcount():
        if estrategia == "aleatoria":
            v = int(rng.integers(h.vcount()))
        elif estrategia == "grado":
            v = int(np.argmax(h.degree()))
        else:
            v = int(np.argmax(h.betweenness(directed=False)))
        orden.append(h.vs[v]["cod"])
        h.delete_vertices(v)
        S.append(gigante(h) / n)
    return np.array(S), orden


def resumen(S):
    f = np.linspace(0, 1, len(S))
    auc = np.trapezoid(S, f)
    f50 = f[np.argmax(S <= S[0] / 2)]
    return auc, f50


curvas, filas, ordenes = {}, [], []
for red, etiqueta in REDES:
    g = cargar(red)
    rng = np.random.default_rng(SEMILLA)
    for est, _ in ESTRATEGIAS:
        if est == "aleatoria":
            reps = np.array([remover(g, est, rng)[0] for _ in range(N_REP)])
            S = reps.mean(axis=0)
            aucs = [resumen(r)[0] for r in reps]
            f50s = [resumen(r)[1] for r in reps]
            auc, f50 = float(np.mean(aucs)), float(np.mean(f50s))
            extra = {"auc_p05": np.quantile(aucs, .05), "auc_p95": np.quantile(aucs, .95)}
        else:
            S, orden = remover(g, est)
            auc, f50 = resumen(S)
            extra = {}
            for pos, c in enumerate(orden[:30], start=1):
                v = g.vs.find(cod=c)
                ordenes.append({"red": red, "estrategia": est, "posicion": pos, "cod": c,
                                "mpio": v["mpio"], "dpto": v["dpto"]})
        curvas[(red, est)] = S
        filas.append({"red": red, "estrategia": est, "N": g.vcount(), "aristas": g.ecount(),
                      "gigante_inicial": S[0], "auc": auc, "f_50": f50,
                      "S_tras_5pct": S[int(round(.05 * g.vcount()))],
                      "S_tras_10pct": S[int(round(.10 * g.vcount()))], **extra})
        print(f"{red:8s} {est:15s} AUC={auc:.3f}  f_50={f50:.3f}")

res = pd.DataFrame(filas)
res.to_csv(RES / "resiliencia_resumen_50km.csv", index=False)
pd.DataFrame(ordenes).to_csv(RES / "resiliencia_orden_remocion_50km.csv", index=False)
largo = max(len(s) for s in curvas.values())
pd.DataFrame({f"{r}_{e}": np.r_[s, [np.nan] * (largo - len(s))] for (r, e), s in curvas.items()}) \
  .assign(f=np.linspace(0, 1, largo)).to_csv(RES / "resiliencia_curvas_50km.csv", index=False)

pd.set_option("display.width", 200)
print("\nRESUMEN")
print(res.round(3).to_string(index=False))
print("\nPrimeros 10 municipios quitados (red general)")
o = pd.DataFrame(ordenes)
for est in ("grado", "intermediacion"):
    sel = o.query("red == 'general' and estrategia == @est").head(10)
    print(f"  {est}: " + ", ".join(f"{m.title()} ({d.title()})" for m, d in zip(sel.mpio, sel.dpto)))

# --- Figura -----------------------------------------------------------------------------
colores = {"aleatoria": "#7f7f7f", "grado": "#2f6db5", "intermediacion": "#c0392b"}
fig, axes = plt.subplots(1, 3, figsize=(16, 4.8), sharey=True)
for ax, (red, etiqueta) in zip(axes, REDES):
    for est, nombre in ESTRATEGIAS:
        S = curvas[(red, est)]
        f = np.linspace(0, 1, len(S))
        auc = res.query("red == @red and estrategia == @est")["auc"].iloc[0]
        ax.plot(f, S, color=colores[est], lw=2, label=f"{nombre} (AUC = {auc:.3f})")
    ax.set_xlim(0, 0.5)
    ax.set_title(f"{etiqueta} (gigante inicial: {curvas[(red, 'grado')][0]:.0%})", fontsize=11)
    ax.set_xlabel("Fracción de municipios quitados")
    ax.grid(alpha=.3)
    ax.legend(fontsize=8.5, frameon=False)
axes[0].set_ylabel("Componente gigante / N inicial")
fig.suptitle(f"Resiliencia de la red de co-ocurrencia (red a {RADIO_KM} km; se muestra hasta quitar el 50 %; "
             f"AUC calculada sobre todo el rango)", fontsize=11.5)
fig.tight_layout()
fig.savefig(FIGS / "resiliencia_50km.png", dpi=150)
print("\nGuardados: resultados/resiliencia_*.csv, figs/resiliencia_50km.png")
