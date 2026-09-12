import os
import pandas as pd
from datetime import datetime

def ejecutar_pruebas_calidad():
    print("Iniciando pruebas automatizadas de calidad de datos (Capa Gold)...")
    ruta_gold = "data/gold"
    ruta_auditoria = "data/auditoria"
    os.makedirs(ruta_auditoria, exist_ok=True)
    
    try:
        dim_clientes = pd.read_parquet(f"{ruta_gold}/dim_clientes.parquet")
        fact_cartera = pd.read_parquet(f"{ruta_gold}/fact_cartera.parquet")
        fact_rentabilidad = pd.read_parquet(f"{ruta_gold}/fact_rentabilidad_cliente.parquet")
    except Exception as e:
        print(f"Error cargando datos: {e}")
        return

    resultados_pruebas = []

    def registrar_resultado(nombre_prueba, descripcion, validacion):
        estado = "APROBADO" if validacion else "FALLÓ"
        resultados_pruebas.append({
            "fecha_ejecucion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "prueba": nombre_prueba,
            "descripcion": descripcion,
            "estado": estado
        })
        print(f"[{estado}] {nombre_prueba}: {descripcion}")

    duplicados_cli = dim_clientes['id_cli'].duplicated().sum()
    registrar_resultado(
        "TEST_01_UNICIDAD",
        "La dimensión clientes no debe tener ID de cliente duplicados",
        duplicados_cli == 0
    )

    nulos_doc = dim_clientes['num_doc'].isnull().sum()
    registrar_resultado(
        "TEST_02_COMPLETITUD",
        "El documento del cliente (enmascarado) no puede ser nulo",
        nulos_doc == 0
    )

    saldos_negativos = fact_cartera[fact_cartera['sdo_capital'] < 0].shape[0]
    registrar_resultado(
        "TEST_03_CONSISTENCIA",
        "Los saldos de capital en cartera no pueden ser negativos",
        saldos_negativos == 0
    )

    clientes_fact = set(fact_cartera['id_cli'].unique())
    clientes_dim = set(dim_clientes['id_cli'].unique())
    huerfanos = clientes_fact - clientes_dim
    registrar_resultado(
        "TEST_04_INTEGRIDAD",
        "Todos los clientes en fact_cartera deben existir en dim_clientes",
        len(huerfanos) == 0
    )

    cltv_negativos = fact_rentabilidad[fact_rentabilidad['cltv_total'] < 0].shape[0]
    registrar_resultado(
        "TEST_05_VALIDEZ",
        "El CLTV total (Rentabilidad) no debe tener valores negativos",
        cltv_negativos == 0
    )

  # Reporte
    df_resultados = pd.DataFrame(resultados_pruebas)
    ruta_reporte = f"{ruta_auditoria}/reporte_pruebas_automatizadas.csv"
    df_resultados.to_csv(ruta_reporte, index=False)
    
    aprobadas = df_resultados[df_resultados['estado'] == 'APROBADO'].shape[0]
    total = df_resultados.shape[0]
    print(f"\nResumen: {aprobadas}/{total} pruebas aprobadas. Reporte exportado a {ruta_reporte}")

if __name__ == "__main__":
    ejecutar_pruebas_calidad()