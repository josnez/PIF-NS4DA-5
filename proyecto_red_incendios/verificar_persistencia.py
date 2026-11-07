import pandas as pd
s = pd.read_csv("resultados/serie_mensual_con_ONI.csv")
print(s.groupby("fase_episodio")["oni"].agg(["min", "max", "count"]))
print("Neutral con |ONI| >= 0.5:", ((s.fase_episodio == "Neutral") & (s.oni.abs() >= 0.5)).sum())



import pandas as pd
s = pd.read_csv("resultados/serie_mensual_con_ONI.csv")
x = s[(s.fase_episodio == "Neutral") & (s.oni.abs() >= 0.5)]
print(x[["anio", "mes", "estacion", "oni", "fase_episodio", "umbral_sin_persistencia"]])