import pandas as pd

datos = {
    "empresa": ["Apple", "Microsoft", "Amazon", "Tesla"],
    "beneficio": [100, 200, 150, 3000]
}

df = pd.DataFrame(datos)

print(df)