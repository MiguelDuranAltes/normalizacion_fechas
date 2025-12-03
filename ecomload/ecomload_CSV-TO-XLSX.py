import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange
from openpyxl import Workbook

# ---------- CONFIGURACIÓN ----------
ruta_csv = "ecomload/colabora.csv"          
ruta_json = "ecomload/id_mapping.json"      
ruta_salida = "ecomload/output_ecomload.csv"
ruta_excel = "ecomload/output_ecomload.xlsx"

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

    # Intentar primero Close Start Date, si no, Production Start Date
    close_start_raw = row.get("Close Start Date")
    prod_start_raw = row.get("Production Start Date")

    fecha_base_raw = None
    origen_fecha = None

    if isinstance(close_start_raw, str) and close_start_raw.strip():
        fecha_base_raw = close_start_raw.strip()
        origen_fecha = "Close Start Date"
    elif isinstance(prod_start_raw, str) and prod_start_raw.strip():
        fecha_base_raw = prod_start_raw.strip()
        origen_fecha = "Production Start Date"
    else:
        print(f"Fila {idx}: sin Close Start Date ni Production Start Date para '{colab}', se omite.")
        continue

    try:
        fecha_base_dt = datetime.strptime(fecha_base_raw, formato_fecha)
    except ValueError:
        print(f"Fila {idx}: ⚠️ formato de fecha no válido '{fecha_base_raw}' en {origen_fecha} para '{colab}', se omite.")
        continue

    # SIEMPRE: Inicio = fecha_base - 58 min (tanto si viene de Close como de Production)
    if origen_fecha == "Close Start Date":
        inicio_dt = fecha_base_dt - timedelta(minutes=58)
    else:  # Production Start Date
        inicio_dt = fecha_base_dt - timedelta(hours=1)

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

# ------ Generar Excel (.xlsx) ------
wb = Workbook()
ws = wb.active

ws.append(["storeId", "Inicio", "Fin", "Comparable"])

for _, r in out_df.iterrows():
    ws.append([r["storeId"], r["Inicio"], r["Fin"], ""])

wb.save(ruta_excel)
print(f"Excel generado correctamente en: {ruta_excel}")