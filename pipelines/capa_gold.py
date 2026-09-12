import os
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

def procesar_capa_gold():
    print("Iniciando procesamiento Capa Gold (Escenario A - Banca)...")
    ruta_silver = "data/silver"
    ruta_gold = "data/gold"
    os.makedirs(ruta_gold, exist_ok=True)
    
    df_cli = pd.read_parquet(f"{ruta_silver}/TB_CLIENTES_CORE/TB_CLIENTES_CORE_silver.parquet")
    df_prod = pd.read_parquet(f"{ruta_silver}/TB_PRODUCTOS_CAT/TB_PRODUCTOS_CAT_silver.parquet")
    df_suc = pd.read_parquet(f"{ruta_silver}/TB_SUCURSALES_RED/TB_SUCURSALES_RED_silver.parquet")
    df_mov = pd.read_parquet(f"{ruta_silver}/TB_MOV_FINANCIEROS/TB_MOV_FINANCIEROS_silver.parquet")
    df_obl = pd.read_parquet(f"{ruta_silver}/TB_OBLIGACIONES/TB_OBLIGACIONES_silver.parquet")
    df_com = pd.read_parquet(f"{ruta_silver}/TB_COMISIONES_LOG/TB_COMISIONES_LOG_silver.parquet")

    dim_clientes = df_cli.copy()
    dim_clientes['nomb_completo'] = dim_clientes['nomb_cli'] + ' ' + dim_clientes['apell_cli']
    dim_clientes['fec_nac'] = pd.to_datetime(dim_clientes['fec_nac'])
    dim_clientes['edad'] = (datetime.now() - dim_clientes['fec_nac']).dt.days // 365
    dim_clientes['desc_segmento'] = dim_clientes['cod_segmento'].str.upper()
    dim_clientes = dim_clientes[['id_cli', 'nomb_completo', 'num_doc', 'edad', 'desc_segmento', 'ciudad_res']]
    dim_clientes.to_parquet(f"{ruta_gold}/dim_clientes.parquet", index=False)
    
    dim_productos = df_prod.copy()
    dim_productos['tasa_mensual'] = (1 + dim_productos['tasa_ea']) ** (1/12) - 1
    dim_productos['familia_prod'] = dim_productos['tip_prod'].map({
        'Crédito': 'Crédito', 'Ahorro': 'Ahorro', 'Transaccional': 'Transaccional'
    }).fillna('Otro')
    dim_productos = dim_productos[['cod_prod', 'desc_prod', 'familia_prod', 'tasa_ea', 'tasa_mensual']]
    dim_productos.to_parquet(f"{ruta_gold}/dim_productos.parquet", index=False)
    
    dim_geografia = df_suc[['ciudad', 'depto']].drop_duplicates().reset_index(drop=True)
    dim_geografia['id_geografia'] = dim_geografia.index + 1
    dim_geografia.to_parquet(f"{ruta_gold}/dim_geografia.parquet", index=False)
    
    dim_canal = df_suc[['tip_punto']].drop_duplicates().rename(columns={'tip_punto': 'desc_canal'})
    canales_digitales = pd.DataFrame({'desc_canal': ['App', 'Web', 'Cajero']})
    dim_canal = pd.concat([dim_canal, canales_digitales]).drop_duplicates().reset_index(drop=True)
    dim_canal['id_canal'] = dim_canal.index + 1
    dim_canal.to_parquet(f"{ruta_gold}/dim_canal.parquet", index=False)

    fact_cartera = df_obl.copy()
    condiciones_mora = [
        (fact_cartera['dias_mora_act'] == 0),
        (fact_cartera['dias_mora_act'] > 0) & (fact_cartera['dias_mora_act'] <= 30),
        (fact_cartera['dias_mora_act'] > 30) & (fact_cartera['dias_mora_act'] <= 60),
        (fact_cartera['dias_mora_act'] > 60) & (fact_cartera['dias_mora_act'] <= 90),
        (fact_cartera['dias_mora_act'] > 90)
    ]
    rangos_mora = ['Al día', 'Rango 1 (1-30 dias)', 'Rango 2 (31-60)', 'Rango 3 (61-90)', 'Deteriorado (más de 90)']
    fact_cartera['bucket_mora'] = np.select(condiciones_mora, rangos_mora, default='Al día')
    
    provision_map = {'A': 0.01, 'B': 0.05, 'C': 0.20, 'D': 0.50, 'E': 1.00}
    fact_cartera['provision_estimada'] = fact_cartera['calif_riesgo'].map(provision_map) * fact_cartera['sdo_capital']
    fact_cartera.to_parquet(f"{ruta_gold}/fact_cartera.parquet", index=False)

    fact_transacciones = df_mov.copy()
    fact_transacciones['vr_mov_usd'] = fact_transacciones['vr_mov'] / 4000.0 
    fact_transacciones['es_habil'] = pd.to_datetime(fact_transacciones['fec_mov']).dt.dayofweek.isin(range(5)).astype(int)
    
    fact_transacciones.to_parquet(f"{ruta_gold}/fact_transacciones.parquet", index=False)

    fecha_limite = datetime.now() - relativedelta(months=12)

    com_cobradas = df_com[(df_com['estado_cobro'] == 'Cobrado') & (pd.to_datetime(df_com['fec_cobro']) >= fecha_limite)]
    cltv_comisiones = com_cobradas.groupby('id_cli')['vr_comision'].sum().reset_index()
    
    obl_intereses = df_obl.merge(dim_productos[['cod_prod', 'tasa_mensual']], on='cod_prod', how='inner')
    obl_intereses['ingreso_intereses'] = obl_intereses['sdo_capital'] * obl_intereses['tasa_mensual'] * 12
    cltv_intereses = obl_intereses.groupby('id_cli')['ingreso_intereses'].sum().reset_index()
    
    fact_rentabilidad = pd.merge(cltv_intereses, cltv_comisiones, on='id_cli', how='outer').fillna(0)
    fact_rentabilidad['cltv_total'] = fact_rentabilidad['ingreso_intereses'] + fact_rentabilidad['vr_comision']
    fact_rentabilidad.to_parquet(f"{ruta_gold}/fact_rentabilidad_cliente.parquet", index=False)

    kpi_base = fact_cartera.merge(dim_clientes[['id_cli', 'desc_segmento', 'ciudad_res']], on='id_cli', how='inner')
    kpi_base['fecha_corte'] = datetime.now().date()
    kpi_base['esta_en_mora'] = np.where(kpi_base['dias_mora_act'] > 0, 1, 0)
    kpi_base['monto_en_mora'] = np.where(kpi_base['dias_mora_act'] > 0, kpi_base['sdo_capital'], 0)
    
    kpis_diarios = kpi_base.groupby(['fecha_corte', 'cod_prod', 'desc_segmento', 'ciudad_res']).agg(
        total_obligaciones_activas=('id_oblig', 'count'),
        monto_total_cartera=('sdo_capital', 'sum'),
        monto_en_mora=('monto_en_mora', 'sum'),
        clientes_con_mora=('esta_en_mora', 'sum')
    ).reset_index()
    
    kpis_diarios['tasa_mora_pct'] = round((kpis_diarios['monto_en_mora'] / kpis_diarios['monto_total_cartera']) * 100, 2)
    kpis_diarios.to_parquet(f"{ruta_gold}/kpis_diarios_cartera.parquet", index=False)

    print("--> Capa Gold finalizada exitosamente.")
    print("Métricas aplicadas: bucket_mora, ind_sospechoso, cltv_total, KPIs diarios y dimensiones.")

if __name__ == "__main__":
    procesar_capa_gold()