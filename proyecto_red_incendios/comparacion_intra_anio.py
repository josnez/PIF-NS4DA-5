import pandas as pd
m = pd.read_csv("resultados/meses_fase.csv")
m = m[m["municipios_activos"] > 0].copy()          # excluye los 3 meses sin registros
m["rel"] = m["municipios_activos"] / m.groupby("anio")["municipios_activos"].transform("mean")
print("Todos los anios:")
print(m.groupby("fase")["rel"].agg(["mean", "median", "count"]).round(2))

c = m.groupby(["anio", "fase"]).size().unstack(fill_value=0)
ok = c[(c["El Nino"] >= 2) & (c["La Nina"] >= 2)].index.tolist()
print("\nAnios con >= 2 meses de El Nino y de La Nina:", ok)
print(m[m.anio.isin(ok)].groupby("fase")["rel"].agg(["mean", "median", "count"]).round(2))