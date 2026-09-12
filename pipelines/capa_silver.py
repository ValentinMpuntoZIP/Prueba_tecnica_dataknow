import os
import pandas as pd
import hashlib
from datetime import datetime

def enmascarar_documento(valor):
    if pd.notnull(valor) and str(valor) != 'nan':
        return hashlib.sha256(str(valor).encode()).hexdigest()
    return valor

def calcular_calidad(df, nombre_tabla, eliminados_dup, rechazados_fk):
    total_inicial = len(df) + eliminados_dup + rechazados_fk
    registros_conformes = len(df)
    pct_conformes = (registros_conformes / total_inicial) * 100 if total_inicial > 0 else 0
    
    nulos_por_columna = df.isnull().sum().to_dict()
    pct_nulos = {k: round((v / registros_conformes * 100), 2) if registros_conformes > 0 else 0 for k, v in nulos_por_columna.items()}
    
    return {
        'fecha_ejecucion': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'tabla': nombre_tabla,
        'total_registros_leidos': total_inicial,
        'duplicados_eliminados': eliminados_dup,
        'huerfanos_rechazados': rechazados_fk,
        'registros_conformes': registros_conformes,
        'porcentaje_conformidad': round(pct_conformes, 2),
        'pct_nulos_por_columna': str(pct_nulos)
    }

def procesar_silver():
    print("Iniciando procesamiento Capa Silver con reglas de gobierno de datos...")
    ruta_bronze = "data/bronze"
    ruta_silver = "data/silver"
    ruta_errores = "data/errores"
    ruta_auditoria = "data/auditoria"
    
    for ruta in [ruta_silver, ruta_errores, ruta_auditoria]:
        os.makedirs(ruta, exist_ok=True)
        
    reporte_calidad = []

    df_cli = pd.read_parquet(f"{ruta_bronze}/TB_CLIENTES_CORE")
    total_cli = len(df_cli)
    df_cli = df_cli.drop_duplicates(subset=['id_cli'], keep='last')
    
  
    df_cli['num_doc'] = df_cli['num_doc'].apply(enmascarar_documento)
    df_cli['nomb_cli'] = '***ENMASCARADO***'
    df_cli['apell_cli'] = '***ENMASCARADO***'
    
    os.makedirs(f"{ruta_silver}/TB_CLIENTES_CORE", exist_ok=True)
    df_cli.to_parquet(f"{ruta_silver}/TB_CLIENTES_CORE/TB_CLIENTES_CORE_silver.parquet", index=False)
    reporte_calidad.append(calcular_calidad(df_cli, 'TB_CLIENTES_CORE', total_cli - len(df_cli), 0))
    valid_clientes = df_cli['id_cli'].unique()
    print(f"--> TB_CLIENTES_CORE procesada. Datos sensibles enmascarados.")


    df_prod = pd.read_parquet(f"{ruta_bronze}/TB_PRODUCTOS_CAT")
    total_prod = len(df_prod)
    df_prod = df_prod.drop_duplicates(subset=['cod_prod'], keep='last')
    
    os.makedirs(f"{ruta_silver}/TB_PRODUCTOS_CAT", exist_ok=True)
    df_prod.to_parquet(f"{ruta_silver}/TB_PRODUCTOS_CAT/TB_PRODUCTOS_CAT_silver.parquet", index=False)
    reporte_calidad.append(calcular_calidad(df_prod, 'TB_PRODUCTOS_CAT', total_prod - len(df_prod), 0))
    valid_productos = df_prod['cod_prod'].unique()

    df_suc = pd.read_parquet(f"{ruta_bronze}/TB_SUCURSALES_RED")
    total_suc = len(df_suc)
    df_suc = df_suc.drop_duplicates(subset=['cod_suc'], keep='last')
    
    os.makedirs(f"{ruta_silver}/TB_SUCURSALES_RED", exist_ok=True)
    df_suc.to_parquet(f"{ruta_silver}/TB_SUCURSALES_RED/TB_SUCURSALES_RED_silver.parquet", index=False)
    reporte_calidad.append(calcular_calidad(df_suc, 'TB_SUCURSALES_RED', total_suc - len(df_suc), 0))
    
    def procesar_tabla_transaccional(nombre_tabla, col_pk, col_fk1, col_fk2):
        df = pd.read_parquet(f"{ruta_bronze}/{nombre_tabla}")
        total_orig = len(df)
        
        df = df.drop_duplicates(subset=[col_pk], keep='last')
        eliminados_dup = total_orig - len(df)
    
        mask_valid = df[col_fk1].isin(valid_clientes) & df[col_fk2].isin(valid_productos)
        df_rechazados = df[~mask_valid].copy()
        df_validos = df[mask_valid].copy()
        rechazados_fk = len(df_rechazados)
    
        if rechazados_fk > 0:
            df_rechazados['motivo_rechazo'] = f'Error FK: Cliente o Producto no existe en dimensiones'
            os.makedirs(f"{ruta_errores}/{nombre_tabla}", exist_ok=True)
            df_rechazados.to_parquet(f"{ruta_errores}/{nombre_tabla}/{nombre_tabla}_errores.parquet", index=False)

        if 'vr_mov' in df_validos.columns:
            df_validos['vr_mov'] = df_validos['vr_mov'].fillna(0.0)
            if nombre_tabla == 'TB_MOV_FINANCIEROS':
                mean_val = df_validos['vr_mov'].mean()
                std_val = df_validos['vr_mov'].std()
                std_val = 0 if pd.isna(std_val) else std_val
                umbral = mean_val + (3 * std_val)
                df_validos['ind_sospechoso'] = np.where(df_validos['vr_mov'] > umbral, 1, 0)
            
        os.makedirs(f"{ruta_silver}/{nombre_tabla}", exist_ok=True)
        df_validos.to_parquet(f"{ruta_silver}/{nombre_tabla}/{nombre_tabla}_silver.parquet", index=False)
        
        reporte_calidad.append(calcular_calidad(df_validos, nombre_tabla, eliminados_dup, rechazados_fk))
        print(f"--> {nombre_tabla} procesada: {len(df_validos)} conformes, {eliminados_dup} duplicados, {rechazados_fk} rechazados por FK.")

        if 'vr_mov' in df_validos.columns:
            df_validos['vr_mov'] = df_validos['vr_mov'].fillna(0.0)
            
        os.makedirs(f"{ruta_silver}/{nombre_tabla}", exist_ok=True)
        df_validos.to_parquet(f"{ruta_silver}/{nombre_tabla}/{nombre_tabla}_silver.parquet", index=False)
        
        reporte_calidad.append(calcular_calidad(df_validos, nombre_tabla, eliminados_dup, rechazados_fk))
        print(f"--> {nombre_tabla} procesada: {len(df_validos)} conformes, {eliminados_dup} duplicados, {rechazados_fk} rechazados por FK.")

    procesar_tabla_transaccional('TB_MOV_FINANCIEROS', 'id_mov', 'id_cli', 'cod_prod')
    procesar_tabla_transaccional('TB_OBLIGACIONES', 'id_oblig', 'id_cli', 'cod_prod')
    procesar_tabla_transaccional('TB_COMISIONES_LOG', 'id_comision', 'id_cli', 'cod_prod')
    
   # Reporte
    df_dq = pd.DataFrame(reporte_calidad)
    ruta_dq = f"{ruta_auditoria}/reporte_calidad_silver.csv"
    
    if os.path.exists(ruta_dq):
        df_dq.to_csv(ruta_dq, mode='a', header=False, index=False)
    else:
        df_dq.to_csv(ruta_dq, index=False)
        
    print(f"\n¡Capa Silver finalizada! Reporte de calidad generado en {ruta_dq}")

if __name__ == "__main__":
    procesar_silver()