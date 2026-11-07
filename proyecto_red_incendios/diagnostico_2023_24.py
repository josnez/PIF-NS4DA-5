import pandas as pd
m = pd.read_csv("resultados/meses_fase.csv")
t = m.groupby("fase")["registros_tabla"].sum()
r = m[m.anio.isin([2023, 2024])].groupby("fase")["registros_tabla"].sum()
print(pd.DataFrame({"total": t, "de_2023_24": r, "porcentaje": (r / t * 100).round(1)}))
sin = m[~m.anio.isin([2023, 2024])].groupby("fase")["municipios_activos"].mean().round(1)
print("Municipios activos/mes sin 2023-24:\n", sin)