import pandas as pd
import json

def formatear_plataforma_B(codigo):
    """
    Convierte 'ZARA_FI' en 'Zara FI'
    """
    marca, region = codigo.split("_")
    marca = marca.capitalize()
    return f"{marca} {region}"

ruta_csv = "data.csv"

# Cargar CSV
df = pd.read_csv(ruta_csv, sep=";", encoding="latin1")

# Necesitamos identificar las columnas reales
# Buscamos aquella que contiene códigos tipo ZARA_FI
col_codigo = None
for col in df.columns:
    if df[col].astype(str).str.contains("ZARA_", na=False).any():
        col_codigo = col
        break

# Buscamos columna país (finlandia, suecia…)
col_pais = None
for col in df.columns:
    if df[col].astype(str).str.contains("FINLANDIA|SUECIA", case=False, na=False).any():
        col_pais = col
        break

if not col_codigo or not col_pais:
    raise Exception("No se encontraron las columnas de código o país.")

diccionario = {}

for _, row in df.iterrows():
    codigo = str(row[col_codigo]).strip()

    if not isinstance(codigo, str) or "_" not in codigo:
        continue

    pais = str(row[col_pais]).strip()

    diccionario[codigo] = {
        "plataforma_A": codigo,
        "plataforma_B": formatear_plataforma_B(codigo),
        "pais_original_archivo": pais
    }

# Guardarlo como JSON
with open("diccionario_paises.json", "w", encoding="utf-8") as f:
    json.dump(diccionario, f, indent=4, ensure_ascii=False)

print("Diccionario generado correctamente:")
print(json.dumps(diccionario, indent=4, ensure_ascii=False))
