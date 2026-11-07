import pandas as pd
m = pd.read_csv("resultados/meses_fase.csv")
m = m[m["municipios_activos"] > 0].copy()
m["rel"] = m["municipios_activos"] / m.groupby("anio")["municipios_activos"].transform("mean")

# 1) Solo los meses de mas reportes (dic-mar), donde ambas fases aparecen
seca = m[m["mes"].isin([12, 1, 2, 3])]
print("Dic-mar, todos los anios:")
print(seca.groupby("fase")["rel"].agg(["mean", "median", "count"]).round(2))

# 2) Quitando el perfil del mes calendario
perfil = m.groupby("mes")["rel"].transform("mean")
m["rel_est"] = m["rel"] / perfil
print("\nRelativo al anio y al mes calendario:")
print(m.groupby("fase")["rel_est"].agg(["mean", "median", "count"]).round(2))

# 3) Cuantos meses de cada fase hay en cada mes calendario
print("\nMeses por fase y mes calendario:")
print(pd.crosstab(m["mes"], m["fase"]))