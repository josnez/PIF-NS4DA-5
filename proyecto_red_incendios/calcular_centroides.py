"""
T06 (parte 1): centroides municipales y pares de municipios a menos de R km.

Entrada : limites_dane/MGN_ADM_MPIO_GRAFICO.shp (capa MGN 2025, EPSG:4326)
Salidas : resultados/centroides_municipios_dane2025.csv
          resultados/pares_candidatos_<R>km.csv   (R = 25, 50, 75)

Los centroides se calculan en EPSG:9377 (MAGNA-SIRGAS Origen Nacional, metros),
no en grados, para que las distancias sean validas.
"""
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

BASE = Path(__file__).resolve().parent
SHP = next(p for p in (BASE / "limites_dane").rglob("*.shp") if "MPIO" in str(p).upper())
SALIDA = BASE / "resultados"
SALIDA.mkdir(exist_ok=True)
RADIOS_KM = (25, 50, 75)

g = gpd.read_file(SHP)
g["cod"] = g["mpio_cdpmp"].astype(str).str.zfill(5)
assert g["cod"].is_unique and g["cod"].str.len().eq(5).all()

p = g.to_crs(9377)                         # CRS metrico
c = p.geometry.centroid
c_wgs = gpd.GeoSeries(c, crs=9377).to_crs(4326)

cent = pd.DataFrame({
    "cod": g["cod"], "dpto": g["dpto_cnmbr"], "mpio": g["mpio_cnmbr"],
    "tipo": g["mpio_tipo"], "area_km2": g["mpio_narea"].round(3),
    "x_m": c.x.round(1), "y_m": c.y.round(1),
    "lon": c_wgs.x.round(5), "lat": c_wgs.y.round(5),
    "centroide_dentro": p.geometry.contains(c).values,
}).sort_values("cod").reset_index(drop=True)
cent.to_csv(SALIDA / "centroides_municipios_dane2025.csv", index=False, encoding="utf-8-sig")
print("Unidades:", len(cent), "| centroide fuera del poligono:", int((~cent.centroide_dentro).sum()))

tree = cKDTree(cent[["x_m", "y_m"]].to_numpy())
for r in RADIOS_KM:
    pr = tree.query_pairs(r * 1000, output_type="ndarray")
    d = np.hypot(*(cent[["x_m", "y_m"]].to_numpy()[pr[:, 0]] - cent[["x_m", "y_m"]].to_numpy()[pr[:, 1]]).T)
    out = pd.DataFrame({"cod_a": cent.cod.to_numpy()[pr[:, 0]],
                        "cod_b": cent.cod.to_numpy()[pr[:, 1]],
                        "dist_km": (d / 1000).round(2)})
    out.to_csv(SALIDA / f"pares_candidatos_{r}km.csv", index=False)
    deg = np.bincount(pr.ravel(), minlength=len(cent))
    print(f"{r} km: pares={len(out)} | sin vecinos={(deg == 0).sum()} | grado medio={deg.mean():.1f}")
