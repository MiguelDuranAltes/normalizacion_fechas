import pandas as pd
import json
from datetime import datetime, timedelta
from calendar import monthrange
from openpyxl import Workbook

# ---------- CONFIGURACIÓN ----------
ruta_xls = "ecomload/colabora.xls"
ruta_json = "ecomload/id_mapping.json"
salida_excel = "ecomload/output_ecomload.xlsx"
salida_csv = "ecomload/output_ecomload.csv"

formato_fecha = "%d/%m/%Y %H:%M"
# -----------------------------------

print("Leyendo archivo XLS desde:", ruta_xls)

df = pd.read_excel(ruta_xls, dtype=str)

# 1) Cargar JSON de mapeo colaboraId -> ecomloadId
print(f"\nLeyendo JSON de mapeo desde: {ruta_json}")
with open(ruta_json, "r", encoding="utf-8") as f:
    data = json.load(f)

map_colabora_to_ecom = {
    item.get("colaboraId"): item.get("ecomloadId")
    for item in data
    if item.get("colaboraId") and item.get("ecomloadId")
}

print(f"Total mapeos cargados: {len(map_colabora_to_ecom)}")


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
        print(f"Fila {idx}: ⚠️ no hay mapeo para '{colab}', se omite.")
        continue

    # Intentar Close Start Date, luego Production Start Date
    close_raw = row.get("Close Start Date")
    prod_raw = row.get("Production Start Date")

    fecha_raw = None
    origen_fecha = None

    if isinstance(close_raw, str) and close_raw.strip():
        fecha_raw = close_raw.strip()
        origen_fecha = "Close Start Date"
    elif isinstance(prod_raw, str) and prod_raw.strip():
        fecha_raw = prod_raw.strip()
        origen_fecha = "Production Start Date"
    else:
        print(f"Fila {idx}: sin fecha válida para '{colab}', se omite.")
        continue

    # Parseo fecha
    try:
        fecha_base = datetime.strptime(fecha_raw, formato_fecha)
    except ValueError:
        print(f"Fila {idx}: ⚠️ fecha inválida '{fecha_raw}' para '{colab}', se omite.")
        continue

    # Inicio
    if origen_fecha == "Close Start Date":
        inicio_dt = fecha_base - timedelta(minutes=58)
    else:
        inicio_dt = fecha_base - timedelta(hours=1)

    # Fin = Inicio + 5 meses
    fin_dt = add_months(inicio_dt, 5)

    rows.append({
        "storeId": ecom_id,
        "Inicio": inicio_dt.strftime(formato_fecha),
        "Fin": fin_dt.strftime(formato_fecha),
    })

# ------ Generar CSV ------
out_df = pd.DataFrame(rows, columns=["storeId", "Inicio", "Fin"])
out_df.to_csv(salida_csv, sep=";", index=False, encoding="utf-8-sig")

print(f"\nCSV generado correctamente en: {salida_csv}")
print(f"Total filas generadas: {len(out_df)}")

# ------ Generar XLSX ------
wb = Workbook()
ws = wb.active

ws.append(["storeId", "Inicio", "Fin", "Comparable"])

for _, r in out_df.iterrows():
    ws.append([r["storeId"], r["Inicio"], r["Fin"], ""])

wb.save(salida_excel)
print(f"Excel XLSX generado correctamente en: {salida_excel}")
