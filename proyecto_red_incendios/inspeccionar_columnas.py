import pandas as pd

c = pd.read_csv("resultados/incendios_consolidados_auditados.csv", low_memory=False)
print("Columnas del consolidado:")
print(list(c.columns))

p = c[c["usar_principal"].astype(str).str.lower().isin(["true", "1"])]
print("\nPrimeras 3 filas del escenario principal:")
print(p.head(3).T)

print("\nPrimeras 5 filas SIN municipio (los 119 casos):")
print(p[p["municipio"].isna()].head(5).T)

s = pd.read_csv("resultados/serie_mensual_con_ONI.csv")
print("\nColumnas de la serie con ONI:")
print(list(s.columns))
print(s.head(3).T)