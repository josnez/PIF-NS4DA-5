"""
T05 (parte 2): agrega la fase ENSO a la tabla municipio-mes y resume actividad por fase.

Entradas (en resultados/):
  - tabla_municipio_mes.csv          (salida de construir_tabla_municipio_mes.py)
  - serie_mensual_con_ONI.csv        (columnas: anio, mes, registros, estado_reporte,
                                      oni, fase_episodio, umbral_sin_persistencia, ...)
Salidas (en resultados/):
  - tabla_municipio_mes_fase.csv     tabla municipio-mes + fase ENSO
  - meses_fase.csv                   una fila por mes (2002-2024) con fase y actividad

La fase oficial es `fase_episodio` (con persistencia de >= 5 trimestres, segun el README).
`umbral_sin_persistencia` se conserva solo para comparar.
"""
from pathlib import Path
import unicodedata
import pandas as pd

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"
ANIO_MIN, ANIO_MAX = 2002, 2024


def fase_estandar(x):
    t = unicodedata.normalize("NFKD", str(x)).encode("ascii", "ignore").decode().lower()
    if "nino" in t or "calido" in t:
        return "El Nino"
    if "nina" in t or "frio" in t:
        return "La Nina"
    if "neutral" in t:
        return "Neutral"
    raise ValueError(f"Fase no reconocida: {x!r}")

tabla = pd.read_csv(RES / "tabla_municipio_mes.csv", dtype={"cod": str})
s = pd.read_csv(RES / "serie_mensual_con_ONI.csv")
print("Valores de fase_episodio:", s["fase_episodio"].unique().tolist())
print("Valores de estado_reporte:", s["estado_reporte"].unique().tolist())

s = s[(s["anio"] >= ANIO_MIN) & (s["anio"] <= ANIO_MAX)].copy()
s["fase"] = s["fase_episodio"].map(fase_estandar)
s["fase_sin_persistencia"] = s["umbral_sin_persistencia"].map(fase_estandar)
s["periodo"] = s["anio"].astype(str) + "-" + s["mes"].astype(int).astype(str).str.zfill(2)
assert s["periodo"].is_unique and len(s) == (ANIO_MAX - ANIO_MIN + 1) * 12, "La serie no tiene 12 meses por anio"

# Union tabla + fase
f = tabla.merge(s[["periodo", "fase", "oni"]], on="periodo", how="left", validate="m:1")
assert f["fase"].notna().all(), "Hay meses de la tabla sin fase"
f.to_csv(RES / "tabla_municipio_mes_fase.csv", index=False)

# Resumen por mes
act = (tabla.groupby("periodo").agg(municipios_activos=("cod", "nunique"),
                                    registros_tabla=("n_registros", "sum")).reset_index())
m = s[["periodo", "anio", "mes", "oni", "fase", "fase_sin_persistencia", "estado_reporte"]].merge(
    act, on="periodo", how="left")
m[["municipios_activos", "registros_tabla"]] = m[["municipios_activos", "registros_tabla"]].fillna(0).astype(int)
m.to_csv(RES / "meses_fase.csv", index=False)

# Verificacion contra el README (79 / 80 / 117 meses y 3 meses sin registros)
print("\nMESES CALENDARIO POR FASE (README: 79 El Nino, 80 La Nina, 117 Neutral)")
print(m["fase"].value_counts().to_string())
print("\nMeses sin ningun municipio activo en la tabla, por fase:")
print(m[m["municipios_activos"] == 0].groupby("fase").size().to_string())
print("\nActividad por fase (descriptivo, SIN ajuste):")
r = m.groupby("fase").agg(meses=("periodo", "size"),
                          mun_activos_media=("municipios_activos", "mean"),
                          mun_activos_mediana=("municipios_activos", "median"),
                          registros_media=("registros_tabla", "mean")).round(1)
r["celdas_municipio_mes"] = m.groupby("fase")["municipios_activos"].sum()
print(r.to_string())
print("\nMeses por anio en cada fase (para ver cuanto pesan 2023-2024):")
print(pd.crosstab(m["anio"], m["fase"]).loc[[2008, 2010, 2016, 2020, 2022, 2023, 2024]].to_string())
print("\nCoincidencia fase con/sin persistencia:")
print(pd.crosstab(m["fase"], m["fase_sin_persistencia"]).to_string())
print("\nGuardados: tabla_municipio_mes_fase.csv y meses_fase.csv")