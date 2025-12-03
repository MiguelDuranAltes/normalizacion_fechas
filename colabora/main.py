import pandas as pd
import pyexcel as p
import json
from datetime import datetime, timedelta
from clean_csv import clean_csv  

# -------------------------
# CONFIGURACIÓN
# -------------------------

ruta_csv_sucio = "original_sucio.csv"
ruta_csv_original = "original.csv"
ruta_json_diccionario = "diccionario_paises.json"
ruta_salida = "colabora.xls"

# -------------------------------------------------------
# EJECUTAR LIMPIEZA DEL CSV ANTES DE TODO
# -------------------------------------------------------

clean_csv(ruta_csv_sucio, ruta_csv_original)

# -------------------------
# LECTURA DE ARCHIVOS
# -------------------------

df = pd.read_csv(ruta_csv_original, encoding="latin1", sep=None, engine="python")

with open(ruta_json_diccionario, "r", encoding="utf-8") as f:
    dicc = json.load(f)

# -------------------------
# MAPA DESDE ecomloadId → info necesaria
# -------------------------

mapa = {}

for entry in dicc:
    ecom = entry["ecomloadId"]
    mapa[ecom] = {
        "colabora": entry["colaboraId"],
        "min": entry.get("data", {}).get("min", 60),         
        "presales": entry.get("data", {}).get("presales", True)
    }

# -------------------------
# CONVERSIÓN DE FECHAS
# -------------------------

MESES = {
    "ene": "jan", "feb": "feb", "mar": "mar", "abr": "apr",
    "may": "may", "jun": "jun", "jul": "jul", "ago": "aug",
    "sep": "sep", "oct": "oct", "nov": "nov", "dic": "dec"
}

def convertir_fecha(fecha_str, hora_str):
    if pd.isna(fecha_str) or pd.isna(hora_str):
        return ""

    fecha_str = str(fecha_str).strip().lower().replace(".", "")
    dia, mes_es = fecha_str.split("-")
    mes_en = MESES.get(mes_es)

    if mes_en is None:
        raise ValueError(f"Mes no reconocido en fecha: {fecha_str}")

    fecha = datetime.strptime(f"{dia}-{mes_en}-2025", "%d-%b-%Y")
    hora = datetime.strptime(hora_str.strip(), "%H:%M")

    dt = datetime(
        fecha.year, fecha.month, fecha.day,
        hora.hour, hora.minute, 0
    )

    return dt.strftime("%d/%m/%Y %I:%M:%S %p")


# -------------------------
# IDENTIFICAR MERCADO CHINA
# -------------------------

def es_mercado_china(code):
    if not isinstance(code, str):
        return False
    code = code.upper()
    return ("_CN" in code) or ("_XD" in code) or ("_XT" in code)


# -------------------------
# PRODUCTION START DATE
# -------------------------

def producir_fecha(fecha_app, hora_web, es_china=False):
    if pd.isna(fecha_app) or pd.isna(hora_web):
        return ""

    fecha_str = str(fecha_app).strip().lower().replace(".", "")
    dia, mes_es = fecha_str.split("-")
    mes_en = MESES.get(mes_es)
    if mes_en is None:
        raise ValueError(f"Mes no reconocido: {fecha_str}")

    fecha = datetime.strptime(f"{dia}-{mes_en}-2025", "%d-%b-%Y")
    hora = datetime.strptime(hora_web.strip(), "%H:%M")

    dt = datetime(
        fecha.year, fecha.month, fecha.day,
        hora.hour, hora.minute, 0
    )

    if es_china:
        dt -= timedelta(minutes=10)

    return dt.strftime("%d/%m/%Y %I:%M:%S %p")


# -------------------------
# CONSTRUCCIÓN DEL EXCEL
# -------------------------

# Crear DataFrame con número correcto de filas
salida = pd.DataFrame(index=range(len(df)))

salida["Event Id"] = ""
salida["Event Type"] = "RV"

# Store Id
salida["Store Id"] = df["CODE"].map(lambda x: mapa.get(x, {}).get("colabora", ""))

salida["Local Time"] = "SI"

# Production Start Date (nueva lógica)
salida["Production Start Date"] = [
    producir_fecha(f_app, h_web, es_mercado_china(code))
    for f_app, h_web, code in zip(df["Fecha Local APP"], df["Hora Local WEB"], df["CODE"])
]

salida["Close Start Date"] = ""

# Close Minutes
salida["Close Minutes"] = df["CODE"].map(lambda x: mapa.get(x, {}).get("min", 60))

# Presales App Hour
salida["Presales App Hour"] = df["CODE"].map(
    lambda x: "" if mapa.get(x, {}).get("presales", True) is False else "1"
)

# Start Date Prewarming
salida["Start Date Prewarming"] = [
    convertir_fecha(f, h) for f, h in zip(df["Fecha Local"], df["Hora Local"])
]

salida["Start Date Prewarming Criteria"] = ""

columnas_en_orden = [
    "Event Id",
    "Event Type",
    "Store Id",
    "Local Time",
    "Production Start Date",
    "Close Start Date",
    "Close Minutes",
    "Presales App Hour",
    "Start Date Prewarming",
    "Start Date Prewarming Criteria"
]

salida = salida[columnas_en_orden]

# -------------------------
# EXPORTACIÓN
# -------------------------

# Crear tabla completamente ordenada
tabla = [columnas_en_orden] + salida[columnas_en_orden].values.tolist()

p.save_as(
    array=tabla,
    dest_file_name=ruta_salida
)
print("Archivo generado:", ruta_salida)
