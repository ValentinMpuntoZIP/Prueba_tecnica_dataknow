import os
import time
import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

def obtener_motor_azure():
    server = os.getenv('DB_SERVER')
    database = os.getenv('DB_DATABASE')
    username = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    driver = "ODBC Driver 18 for SQL Server"
    
    conn_str = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
    return create_engine(conn_str, fast_executemany=True)

def ingestar_tabla_a_bronze(nombre_tabla, engine, batch_id):
    print(f"Ingestando {nombre_tabla} a la capa Bronze (Incremental)...")
    start_time = time.time()
    
    os.makedirs("data/auditoria", exist_ok=True)
    watermark_file = f"data/auditoria/watermark_{nombre_tabla}.txt"
    ultima_fecha = "1900-01-01 00:00:00"

    if os.path.exists(watermark_file):
        with open(watermark_file, "r") as f:
            ultima_fecha = f.read().strip()

    campo_fecha = {
        "TB_CLIENTES_CORE": "fec_nac",    
        "TB_PRODUCTOS_CAT": None,            
        "TB_MOV_FINANCIEROS": "fec_mov",
        "TB_OBLIGACIONES": "fec_desembolso", 
        "TB_SUCURSALES_RED": None,
        "TB_COMISIONES_LOG": "fec_comision"
    }.get(nombre_tabla, None)

    if campo_fecha and ultima_fecha != "1900-01-01 00:00:00":
        query = f"SELECT * FROM {nombre_tabla} WHERE {campo_fecha} > '{ultima_fecha}'"
    else:
        query = f"SELECT * FROM {nombre_tabla}"

    df = pd.read_sql(query, engine)
    registros = len(df)
    
    ahora = datetime.now()
    df['_ingestion_timestamp'] = ahora
    df['_source_system'] = 'Azure SQL'
    df['_batch_id'] = batch_id
    
    df['year'] = ahora.strftime('%Y')
    df['month'] = ahora.strftime('%m')
    df['day'] = ahora.strftime('%d')
    
    ruta_bronze = f"data/bronze/{nombre_tabla}"
    os.makedirs(ruta_bronze, exist_ok=True)
    
    if registros > 0:
        df.to_parquet(
            ruta_bronze, 
            index=False, 
            partition_cols=['year', 'month', 'day'],
            engine='pyarrow'
        )
        
        if campo_fecha and campo_fecha in df.columns:
            max_fecha = df[campo_fecha].max()
            if pd.notna(max_fecha):
                with open(watermark_file, "w") as f:
                    f.write(str(max_fecha))

    duracion = round(time.time() - start_time, 2)
    tamaño_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
    
    log_record = {
        'fecha_ejecucion': ahora.strftime('%Y-%m-%d %H:%M:%S'),
        'batch_id': batch_id,
        'tabla': nombre_tabla,
        'registros_procesados': registros,
        'tamano_mb': round(tamaño_mb, 2),
        'duracion_segundos': duracion
    }
    return log_record

def main():
    print("Iniciando Ingesta Incremental a Capa Bronze...")
    engine = obtener_motor_azure()
    batch_id = datetime.now().strftime("%Y%m%d%H%M%S")
    
    tablas = [
        "TB_CLIENTES_CORE", 
        "TB_PRODUCTOS_CAT", 
        "TB_MOV_FINANCIEROS",
        "TB_OBLIGACIONES",
        "TB_SUCURSALES_RED",
        "TB_COMISIONES_LOG"
    ]
    
    logs = []
    for tabla in tablas:
        log = ingestar_tabla_a_bronze(tabla, engine, batch_id)
        logs.append(log)
        
    df_logs = pd.DataFrame(logs)
    os.makedirs("data/auditoria", exist_ok=True)
    ruta_log = "data/auditoria/log_bronze_ingest.csv"
    
    if os.path.exists(ruta_log):
        df_logs.to_csv(ruta_log, mode='a', header=False, index=False)
    else:
        df_logs.to_csv(ruta_log, index=False)
        
    print(f"¡Ingesta incremental a Bronze finalizada! Log guardado en {ruta_log}")

if __name__ == "__main__":
    main()