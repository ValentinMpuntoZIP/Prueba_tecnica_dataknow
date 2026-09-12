import subprocess
import sys
import pandas as pd
import os
from datetime import datetime

def ejecutar_script(ruta_script):
    print(f"\n[ORQUESTADOR] Ejecutando: {ruta_script}...")
    resultado = subprocess.run([sys.executable, ruta_script], capture_output=False)
    if resultado.returncode != 0:
        print(f"ALERTA CRÍTICA: Fallo en la tarea {ruta_script} a las {datetime.now()}.")
        sys.exit(1)

def verificar_anomalia_volumen():
    ruta_log = "data/auditoria/log_bronze_ingest.csv"
    if not os.path.exists(ruta_log):
        return
        
    df_logs = pd.read_csv(ruta_log)
    if len(df_logs) < 2:
        return
    
    ultimos_registros = df_logs.tail(7)['registros_procesados'].mean()
    volumen_actual = df_logs.iloc[-1]['registros_procesados']
    
    variacion = abs(volumen_actual - ultimos_registros) / ultimos_registros

    if variacion > 0.30:
        print(f"\n[ALERTA DE ANOMALÍA] Variación de volumen superior al 30%. Promedio: {ultimos_registros}, Actual: {volumen_actual}")

def generar_reporte_diario():
    print("\n==================================================")
    print("      REPORTE DIARIO DE EJECUCIÓN DEL PIPELINE    ")
    print("==================================================")
    print(f"Fecha de finalización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Estado General: EXITOSO")
    
    if os.path.exists("data/auditoria/log_bronze_ingest.csv"):
        df_b = pd.read_csv("data/auditoria/log_bronze_ingest.csv")
        print(f"Total registros ingestados (Bronze): {df_b['registros_procesados'].sum()}")
        
    if os.path.exists("data/auditoria/reporte_calidad_silver.csv"):
        df_s = pd.read_csv("data/auditoria/reporte_calidad_silver.csv")
        rechazados = df_s['huerfanos_rechazados'].sum()
        conformes = df_s['registros_conformes'].sum()
        print(f"Total registros conformes (Silver): {conformes}")
        print(f"Alertas de calidad (Registros rechazados): {rechazados}")
    print("==================================================")

def main():
    print("=== INICIANDO PIPELINE AUTOMATIZADO ===")
    
    # Ejecución pipeline
    ejecutar_script("pipelines/capa_bronze.py")
    ejecutar_script("pipelines/capa_silver.py")
    ejecutar_script("pipelines/capa_gold.py")
    
    # QA
    ejecutar_script("pipelines/qa_tests.py")
    
    #Alertas
    verificar_anomalia_volumen()
    generar_reporte_diario()

if __name__ == "__main__":
    main()