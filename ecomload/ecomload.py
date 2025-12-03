import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange

# ---------- CONFIGURACIÓN ----------
ruta_csv = "ecomload/colabora.csv"          # CSV de eventos
ruta_json = "ecomload/id_mapping.json"      # JSON con baseId / colaboraId / ecomloadId
ruta_salida = "ecomload/ecomload_output.csv"

formato_fecha = "%d/%m/%Y %H:%M"
# -----------------------------------

print("Leyendo CSV de eventos desde:", ruta_csv)

df = pd.read_csv(
    ruta_csv,
    sep=",",          # el CSV de eventos viene separado por comas
    engine="python",
    dtype=str
)

# 1) Cargar JSON de mapeo colaboraId -> ecomloadId
print(f"\nLeyendo JSON de mapeo desde: {ruta_json}")
with open(ruta_json, "r", encoding="utf-8") as f:
    data = json.load(f)

map_colabora_to_ecom = {}
for item in data:
    colab = item.get("colaboraId")
    ecom = item.get("ecomloadId")
    if colab and ecom:
        map_colabora_to_ecom[colab] = ecom

print(f"Total mapeos colaboraId -> ecomloadId cargados: {len(map_colabora_to_ecom)}")

def add_months(dt, months):
    month = dt.month - 1 + months
    year = dt.year + month // 12
    month = month % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)

rows = []

for idx, row in df.iterrows():
    colab = row.get("Store Id")

    if not isinstance(colab, str) or not colab.strip():
        print(f"Fila {idx}: sin Store Id, se omite.")
        continue

    colab = colab.strip()

    ecom_id = map_colabora_to_ecom.get(colab)
    if not ecom_id:
        print(f"Fila {idx}: ⚠️ no encontré mapeo en el JSON para colaboraId = '{colab}', se omite.")
        continue

    close_start_raw = row.get("Close Start Date")

    if not isinstance(close_start_raw, str) or not close_start_raw.strip():
        print(f"Fila {idx}: ⚠️ sin Close Start Date para '{colab}', se omite.")
        continue

    close_start_raw = close_start_raw.strip()

    try:
        close_dt = datetime.strptime(close_start_raw, formato_fecha)
    except ValueError:
        print(f"Fila {idx}: ⚠️ formato de fecha no válido '{close_start_raw}' para '{colab}', se omite.")
        continue

    # 👉 SIEMPRE: Inicio = Close Start Date - 58 min
    inicio_dt = close_dt - timedelta(minutes=58)

    # Fin = Inicio + 5 meses
    fin_dt = add_months(inicio_dt, 5)

    rows.append({
        "storeId": ecom_id,
        "Inicio": inicio_dt.strftime(formato_fecha),
        "Fin": fin_dt.strftime(formato_fecha),
    })

out_df = pd.DataFrame(rows, columns=["storeId", "Inicio", "Fin"])
out_df.to_csv(ruta_salida, sep=";", index=False, encoding="utf-8-sig")

print(f"\nCSV generado correctamente en: {ruta_salida}")
print(f"Total filas generadas: {len(out_df)}")
