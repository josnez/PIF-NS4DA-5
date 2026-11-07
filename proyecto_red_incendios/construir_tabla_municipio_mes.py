"""
T05 (parte 1): tabla municipio-mes a partir del consolidado auditado.

Entradas (en resultados/):
  - incendios_consolidados_auditados.csv
  - equivalencia_base_dane.csv   (salida de exportar_divipola.py)
Salidas (en resultados/):
  - tabla_municipio_mes.csv        una fila por municipio (codigo DANE) y mes con >= 1 registro
  - meses_activos_por_municipio.csv
Imprime una cascada de filtros para documentar cuantos registros se pierden y por que.

Decisiones (parametros editables abajo):
  D1: escenario principal (usar_principal), anios ANIO_MIN..ANIO_MAX, con mes recuperable.
  D2: un municipio esta "activo" un mes si tiene >= MIN_REG_ACTIVO registros.
La fase ENSO NO se agrega aqui: se une en la parte 2, cuando se conozca la estructura
de serie_mensual_con_ONI.
"""
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent
RES = BASE / "resultados"
ANIO_MIN, ANIO_MAX = 2002, 2024
MIN_REG_ACTIVO = 1

c = pd.read_csv(RES / "incendios_consolidados_auditados.csv", low_memory=False)
eq = pd.read_csv(RES / "equivalencia_base_dane.csv", dtype={"codigo_mpio": str})

# --- Cascada de filtros -------------------------------------------------------
pasos = [("Filas totales del archivo", len(c))]
c = c[c["usar_principal"].astype(str).str.lower().isin(["true", "1"])].copy()
pasos.append(("Escenario principal (usar_principal)", len(c)))
c = c[(c["anio"] >= ANIO_MIN) & (c["anio"] <= ANIO_MAX)]
pasos.append((f"Anios {ANIO_MIN}-{ANIO_MAX}", len(c)))
c = c[c["mes"].notna()].copy()
pasos.append(("Con mes recuperable", len(c)))

# Codigo DANE por (departamento, municipio) de la base
llaves = eq[["departamento", "municipio", "codigo_mpio"]].drop_duplicates(["departamento", "municipio"])
c = c.merge(llaves, on=["departamento", "municipio"], how="left")
c = c[c["codigo_mpio"].notna()].copy()
pasos.append(("Con codigo DANE", len(c)))

print("CASCADA DE FILTROS")
anterior = None
for nombre, n in pasos:
    perdida = "" if anterior is None else f"  (-{anterior - n})"
    print(f"  {nombre:<42}{n:>8}{perdida}")
    anterior = n

# --- Tabla municipio-mes ----------------------------------------------------------
c["mes"] = c["mes"].astype(int)
tabla = (c.groupby(["codigo_mpio", "anio", "mes"], as_index=False)
           .size().rename(columns={"size": "n_registros", "codigo_mpio": "cod"}))
tabla = tabla[tabla["n_registros"] >= MIN_REG_ACTIVO].copy()
tabla["periodo"] = tabla["anio"].astype(str) + "-" + tabla["mes"].astype(str).str.zfill(2)
tabla = tabla.sort_values(["periodo", "cod"]).reset_index(drop=True)
tabla.to_csv(RES / "tabla_municipio_mes.csv", index=False)

act = (tabla.groupby("cod").agg(meses_activos=("periodo", "nunique"),
                                registros=("n_registros", "sum")).reset_index())
act.to_csv(RES / "meses_activos_por_municipio.csv", index=False)

n_meses_posibles = (ANIO_MAX - ANIO_MIN + 1) * 12
print("\nTABLA MUNICIPIO-MES")
print("  Filas (municipio-mes activos):", len(tabla))
print("  Municipios (codigos) con >= 1 mes activo:", act["cod"].nunique())
print(f"  Meses distintos con actividad: {tabla['periodo'].nunique()} de {n_meses_posibles}")
print("  Municipios activos por mes:", tabla.groupby("periodo")["cod"].nunique().describe().round(1).to_dict())
print("  Meses activos por municipio:", act["meses_activos"].describe().round(1).to_dict())
print("  Municipios con un solo mes activo:", int((act["meses_activos"] == 1).sum()))
print("\nGuardados: tabla_municipio_mes.csv y meses_activos_por_municipio.csv")