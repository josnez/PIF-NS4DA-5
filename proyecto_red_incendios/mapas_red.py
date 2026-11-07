"""
T17 (version preliminar) y T18: mapas de la red de co-ocurrencia de incendios sobre Colombia.

Figura 1  mapas_red_general_50km.png : red general (nodos en centroides municipales, aristas podadas).
Figura 2  mapas_red_fases_50km.png   : El Nino, La Nina y Neutral lado a lado, con la MISMA escala
                                       de tamano, color y umbral de aristas (para poder compararlas).

Codificacion (se repite en cada figura):
  - Posicion  : centroide del municipio (no el punto del incendio).
  - Tamano    : meses con actividad (en la figura 2, meses con actividad dentro de la fase).
  - Color     : grado del nodo en la red DIBUJADA (aristas podadas), no en la red completa.
  - Lineas    : solo aristas con w >= umbral de dibujo; el grosor crece con el peso.
Las figuras son descriptivas: una linea indica co-ocurrencia de registros, no propagacion.
Cuando B entregue las comunidades (T12) y los puentes (T13), se agrega una version con color
por comunidad y los puentes resaltados.

Entradas: limites_dane/ (capa MGN), resultados/centroides_municipios_dane2025.csv,
          resultados/aristas_general_50km.csv, aristas_<fase>_50km.csv,
          resultados/tabla_municipio_mes.csv, tabla_municipio_mes_fase.csv
Salidas : figs/mapas_red_general_50km.png, figs/mapas_red_fases_50km.png
Requiere: pip install matplotlib
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection

BASE = Path(__file__).resolve().parent
RES, FIGS = BASE / "resultados", BASE / "figs"
FIGS.mkdir(exist_ok=True)
RADIO_KM = 50
W_MIN_GENERAL = 5          # red general: se dibujan aristas con >= 5 meses en comun
W_PROP_MIN_FASE = 0.03     # fases: aristas con co-actividad en >= 3 % de los meses de la fase
FASES = [("El Nino", "El Niño"), ("La Nina", "La Niña"), ("Neutral", "Neutral")]
XLIM, YLIM = (-79.6, -66.4), (-4.4, 13.6)      # San Andres queda fuera del recuadro

# --- Contorno departamental ---------------------------------------------------------------
shp = next(p for p in (BASE / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
dptos = gpd.read_file(shp)[["dpto_ccdgo", "geometry"]].dissolve(by="dpto_ccdgo")
dptos["geometry"] = dptos.geometry.simplify(0.01)

cent = pd.read_csv(RES / "centroides_municipios_dane2025.csv", dtype={"cod": str}).set_index("cod")


def base_mapa(ax):
    dptos.plot(ax=ax, color="#f3f1ec", edgecolor="#b9b5aa", linewidth=0.4)
    ax.set_xlim(*XLIM); ax.set_ylim(*YLIM)
    ax.set_aspect(1 / np.cos(np.radians(4.5)))
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)


def dibujar(ax, aristas, wcol, umbral, meses_nodo, vmax_color, escala_tam, wmax):
    """Dibuja aristas con wcol >= umbral y nodos activos. Devuelve (scatter, n_aristas)."""
    a = aristas[aristas[wcol] >= umbral]
    xa, ya = cent.loc[a.cod_a, ["lon", "lat"]].to_numpy().T
    xb, yb = cent.loc[a.cod_b, ["lon", "lat"]].to_numpy().T
    segs = np.stack([np.c_[xa, ya], np.c_[xb, yb]], axis=1)
    lw = 0.25 + 1.1 * (a[wcol].to_numpy() / wmax)
    ax.add_collection(LineCollection(segs, colors="#4a4a4a", linewidths=lw, alpha=0.22, zorder=2))
    grado = pd.concat([a.cod_a, a.cod_b]).value_counts()
    nodos = meses_nodo[meses_nodo > 0].index
    d = grado.reindex(nodos).fillna(0)
    orden = d.sort_values().index                       # los de mayor grado quedan encima
    xy = cent.loc[orden, ["lon", "lat"]].to_numpy()
    sc = ax.scatter(xy[:, 0], xy[:, 1], s=4 + escala_tam * meses_nodo[orden].to_numpy(),
                    c=d[orden].to_numpy(), cmap="viridis", vmin=0, vmax=vmax_color,
                    edgecolors="white", linewidths=0.25, alpha=0.95, zorder=3)
    return sc, len(a)


def leyenda_tamanos(ax, escala_tam, valores):
    for v in valores:
        ax.scatter([], [], s=4 + escala_tam * v, c="#9a9a9a", edgecolors="white", label=f"{v} meses")
    ax.legend(title="Meses con actividad", loc="lower left", fontsize=7, title_fontsize=7,
              frameon=False, labelspacing=1.1)


# --- Figura 1: red general ---------------------------------------------------------------------
tabla = pd.read_csv(RES / "tabla_municipio_mes.csv", dtype={"cod": str})
meses_nodo = tabla.groupby("cod")["periodo"].nunique()
ar = pd.read_csv(RES / f"aristas_general_{RADIO_KM}km.csv", dtype={"cod_a": str, "cod_b": str})
esc = 1.4
fig, ax = plt.subplots(figsize=(7.2, 8.4), dpi=200)
base_mapa(ax)
grado_max = pd.concat([ar[ar.w_meses >= W_MIN_GENERAL].cod_a, ar[ar.w_meses >= W_MIN_GENERAL].cod_b]).value_counts().max()
sc, n_dib = dibujar(ax, ar, "w_meses", W_MIN_GENERAL, meses_nodo, grado_max, esc, ar["w_meses"].max())
cb = fig.colorbar(sc, ax=ax, shrink=0.55, pad=0.01)
cb.set_label("Grado en la red dibujada", fontsize=8)
cb.ax.tick_params(labelsize=7)
leyenda_tamanos(ax, esc, [5, 30, 100])
ax.set_title(f"Red de co-ocurrencia de incendios, municipios a menos de {RADIO_KM} km (2002-2024)\n"
             f"{len(meses_nodo)} municipios; se dibujan {n_dib:,} de {len(ar):,} aristas (≥ {W_MIN_GENERAL} meses en común)".replace(",", "."),
             fontsize=9)
fig.text(0.5, 0.035, "Nodo = centroide municipal. Línea = co-ocurrencia de registros en el mismo mes, no propagación.\n"
         "San Andrés y Providencia quedan fuera del recuadro.", ha="center", fontsize=7, color="#555")
fig.savefig(FIGS / f"mapas_red_general_{RADIO_KM}km.png", bbox_inches="tight")
plt.close(fig)
print(f"Figura 1: {n_dib} aristas dibujadas de {len(ar)} (umbral w >= {W_MIN_GENERAL}); grado maximo dibujado = {grado_max}")

# --- Figura 2: tres fases con la misma escala -------------------------------------------------------
tf = pd.read_csv(RES / "tabla_municipio_mes_fase.csv", dtype={"cod": str})
datos, gmax, wmax = {}, 0, 0
for f, _ in FASES:
    a = pd.read_csv(RES / f"aristas_{f.replace(' ', '_')}_{RADIO_KM}km.csv", dtype={"cod_a": str, "cod_b": str})
    mf = tf[tf.fase == f].groupby("cod")["periodo"].nunique()
    sel = a[a.w_prop >= W_PROP_MIN_FASE]
    gmax = max(gmax, pd.concat([sel.cod_a, sel.cod_b]).value_counts().max())
    wmax = max(wmax, a["w_prop"].max())
    datos[f] = (a, mf)

esc2 = 2.2
fig, axes = plt.subplots(1, 3, figsize=(14, 6.2), dpi=200)
for ax, (f, nombre) in zip(axes, FASES):
    a, mf = datos[f]
    base_mapa(ax)
    sc, n_dib = dibujar(ax, a, "w_prop", W_PROP_MIN_FASE, mf, gmax, esc2, wmax)
    n_act = int((mf > 0).sum())
    ax.set_title(f"{nombre}\n{n_act} municipios activos · {n_dib:,} aristas dibujadas de {len(a):,}".replace(",", "."), fontsize=9)
    print(f"Figura 2 - {f}: {n_dib} aristas dibujadas de {len(a)}; municipios activos = {n_act}")
leyenda_tamanos(axes[0], esc2, [3, 15, 40])
cb = fig.colorbar(sc, ax=axes, shrink=0.6, pad=0.01, fraction=0.02)
cb.set_label("Grado en la red dibujada (misma escala en los tres mapas)", fontsize=8)
cb.ax.tick_params(labelsize=7)
fig.suptitle(f"Redes por fase ENSO, municipios a menos de {RADIO_KM} km. Se dibujan las aristas con co-actividad en ≥ {W_PROP_MIN_FASE:.0%} de los meses de la fase",
             fontsize=10, y=0.98)
fig.text(0.5, 0.02, "Los mapas comparan estructura, no intensidad: El Niño tiene más celdas municipio-mes (7.695) que La Niña (3.128). "
         "La fase está mezclada con el año de reporte.", ha="center", fontsize=7.5, color="#555")
fig.savefig(FIGS / f"mapas_red_fases_{RADIO_KM}km.png", bbox_inches="tight")
plt.close(fig)
print("\nGuardados en figs/: mapas_red_general_50km.png y mapas_red_fases_50km.png")