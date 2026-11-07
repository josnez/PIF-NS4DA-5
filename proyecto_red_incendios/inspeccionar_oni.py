import pandas as pd
s = pd.read_csv("resultados/serie_mensual_con_ONI.csv")
print(list(s.columns)); print(s.head(3).T); print(s.shape)