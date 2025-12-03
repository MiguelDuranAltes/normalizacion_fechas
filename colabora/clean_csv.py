import pandas as pd

def clean_csv(ruta_entrada, ruta_salida):

    # ------------------------------
    # 1) LEER EL CSV SUCIO
    # ------------------------------
    with open(ruta_entrada, "r", encoding="latin1") as f:
        lineas = f.readlines()

    # Buscar la fila de cabecera que contiene PAIS
    indice_header = None
    for i, linea in enumerate(lineas):
        if "PAIS" in linea and ";" in linea:
            indice_header = i
            break

    if indice_header is None:
        raise Exception("No se encontró fila con 'PAIS'.")

    # Recortar desde la cabecera
    lineas_limpias = lineas[indice_header:]

    # Reemplazar segunda columna por CODE
    cols = lineas_limpias[0].strip().split(";")
    if len(cols) > 1:
        cols[1] = "CODE"
    lineas_limpias[0] = ";".join(cols) + "\n"

    # Guardar temporal
    with open(ruta_salida, "w", encoding="latin1") as f:
        f.writelines(lineas_limpias)

    # ------------------------------
    # 2) CARGAR COMO DATAFRAME LIMPIO
    # ------------------------------
    df = pd.read_csv(ruta_salida, sep=";", encoding="latin1")

    # Eliminar filas/columnas vacías
    df = df.dropna(how="all", axis=1)
    df = df.dropna(how="all", axis=0)

    # La última columna es "Mercado"
    ultima = df.columns[-1]
    df = df.rename(columns={ultima: "Mercado"})

    # ------------------------------
    # 3) REGLAS DE CHINA (ZARA_CN)
    # ------------------------------

    # 3.1 Eliminar fila WeChat
    mask_wechat = df["Mercado"].astype(str).str.contains("wechat", case=False, na=False)
    df = df[~mask_wechat].reset_index(drop=True)

    # 3.2 Localizar fila Douyin/Tmall
    mask_douyin = df["Mercado"].astype(str).str.contains("douyin|tmall", case=False, na=False)
    indices_douyin = df.index[mask_douyin].tolist()

    if indices_douyin:
        idx = indices_douyin[0]
        base = df.loc[[idx]].copy()

        xd = base.copy()
        xt = base.copy()

        xd["CODE"] = "ZARA_XD"
        xt["CODE"] = "ZARA_XT"

        df = df.drop(index=idx).reset_index(drop=True)

        df_upper = df.iloc[:idx]
        df_lower = df.iloc[idx:]

        df = pd.concat([df_upper, xd, xt, df_lower], ignore_index=True)

    # ------------------------------
    # 4) DUPLICACIÓN DE ZARA_AE (solo si no existe ZARA_XE)
    # ------------------------------

    if not (df["CODE"] == "ZARA_XE").any():

        fila_ae = df[df["CODE"] == "ZARA_AE"]

        if not fila_ae.empty:
            nueva = fila_ae.copy()

            nueva["CODE"] = "ZARA_XE"
            nueva["PAIS"] = "ABU DABHI"

            for idx in reversed(fila_ae.index.tolist()):
                df = pd.concat([
                    df.iloc[:idx+1],
                    nueva,
                    df.iloc[idx+1:]
                ]).reset_index(drop=True)

    # ------------------------------
    # 5) GUARDAR CSV FINAL LIMPIO
    # ------------------------------

    df.to_csv(ruta_salida, index=False, sep=";", encoding="latin1")
    print("CSV limpio generado en:", ruta_salida)
