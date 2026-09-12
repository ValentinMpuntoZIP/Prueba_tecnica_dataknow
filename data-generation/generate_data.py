import pandas as pd
import numpy as np
from faker import Faker
import yaml
import os
import random
from sqlalchemy import create_engine
from datetime import datetime, timedelta
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
server = os.getenv('DB_SERVER')
database = os.getenv('DB_DATABASE')
username = os.getenv('DB_USER')
password = os.getenv('DB_PASSWORD')

BASE_DIR = Path(__file__).resolve().parent
config_path = BASE_DIR / 'config.yaml'

with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

seed_value = config['generation']['seed']
Faker.seed(seed_value)
np.random.seed(seed_value)
random.seed(seed_value)
fake = Faker('es_CO')

driver = config['generation']['database_target']['driver']

def generar_clientes(volumen):
    data = []
    segmentos = ['Básico', 'Estándar', 'Premium', 'Elite']
    for i in range(1, volumen + 1):
        data.append({
            'id_cli': i,
            'nomb_cli': fake.first_name(),
            'apell_cli': fake.last_name(),
            'tip_doc': random.choice(['CC', 'CE', 'Pasaporte']),
            'num_doc': fake.unique.random_number(digits=10),
            'fec_nac': fake.date_of_birth(minimum_age=18, maximum_age=80),
            'fec_alta': fake.date_between(start_date='-5y', end_date='today'),
            'cod_segmento': random.choice(segmentos),
            'score_buro': random.randint(300, 850),
            'ciudad_res': fake.city(),
            'depto_res': random.choice(['Antioquia', 'Cundinamarca', 'Valle del Cauca', 'Atlántico', 'Santander', 'Bolívar', 'Risaralda']),
            'estado_cli': random.choice(['Activo', 'Inactivo', 'Bloqueado']),
            'canal_adquis': random.choice(['App', 'Web', 'Sucursal'])
        })
    return pd.DataFrame(data)

def generar_productos(volumen):
    data = []
    tipos = ['Crédito', 'Ahorro', 'Transaccional']
    for i in range(1, volumen + 1):
        data.append({
            'cod_prod': f'PROD_{i}',
            'desc_prod': fake.catch_phrase(),
            'tip_prod': random.choice(tipos),
            'tasa_ea': round(random.uniform(0.01, 0.28), 4),
            'plazo_max_meses': random.choice([12, 24, 36, 48, 60, 72]),
            'cuota_min': round(random.uniform(10000, 50000), 2),
            'comision_admin': round(random.uniform(0, 5000), 2),
            'estado_prod': 'Activo'
        })
    return pd.DataFrame(data)

def generar_movimientos(volumen, clientes_df, productos_df):
    data = []
    for i in range(1, volumen + 1):
        data.append({
            'id_mov': i,
            'id_cli': random.choice(clientes_df['id_cli']),
            'cod_prod': random.choice(productos_df['cod_prod']),
            'num_cuenta': fake.iban(),
            'fec_mov': (datetime.now() - timedelta(days=random.randint(0, 365))).date(),
            'hra_mov': fake.time(),
            'vr_mov': round(random.uniform(5000, 5000000), 2),
            'tip_mov': random.choice(['Pago', 'Transferencia', 'Retiro', 'Consignación']),
            'cod_canal': random.choice(['C01', 'C02', 'C03']), # App, Web, Cajero
            'cod_ciudad': random.randint(1, 100),
            'cod_estado_mov': random.choice(['Exitoso', 'Rechazado', 'Pendiente']),
            'id_dispositivo': fake.uuid4()
        })
    return pd.DataFrame(data)

def generar_obligaciones(volumen, clientes_df, productos_df):
    data = []
    for i in range(1, volumen + 1):
        vr_aprobado = round(random.uniform(1000000, 50000000), 2)
        data.append({
            'id_oblig': i,
            'id_cli': random.choice(clientes_df['id_cli']),
            'cod_prod': random.choice(productos_df['cod_prod']),
            'vr_aprobado': vr_aprobado,
            'vr_desembolsado': vr_aprobado,
            'sdo_capital': round(vr_aprobado * random.uniform(0.1, 0.9), 2),
            'vr_cuota': round(vr_aprobado / random.choice([12, 24, 36, 48, 60]), 2),
            'fec_desembolso': fake.date_between(start_date='-3y', end_date='today'),
            'fec_venc': fake.date_between(start_date='today', end_date='+5y'),
            'dias_mora_act': random.choice([0, 0, 0, 15, 45, 75, 120]),
            'num_cuotas_pend': random.randint(1, 60),
            'calif_riesgo': random.choice(['A', 'B', 'C', 'D', 'E'])
        })
    return pd.DataFrame(data)

def generar_sucursales(volumen):
    data = []
    for i in range(1, volumen + 1):
        data.append({
            'cod_suc': f'SUC_{i}',
            'nom_suc': f'Sucursal {fake.city()}',
            'tip_punto': random.choice(['Físico', 'Corresponsal']),
            'ciudad': fake.city(),
            'depto': random.choice(['Antioquia', 'Cundinamarca', 'Valle del Cauca']),
            'latitud': float(fake.latitude()),
            'longitud': float(fake.longitude()),
            'activo': 1
        })
    return pd.DataFrame(data)

def generar_comisiones(volumen, clientes_df, productos_df):
    data = []
    for i in range(1, volumen + 1):
        data.append({
            'id_comision': i,
            'id_cli': random.choice(clientes_df['id_cli']),
            'cod_prod': random.choice(productos_df['cod_prod']),
            'fec_cobro': fake.date_between(start_date='-1y', end_date='today'),
            'vr_comision': round(random.uniform(1000, 50000), 2),
            'tip_comision': random.choice(['Manejo', 'Retiro', 'Transferencia']),
            'estado_cobro': random.choice(['Cobrado', 'Pendiente', 'Exonerado'])
        })
    return pd.DataFrame(data)

def inyectar_anomalias(df, tabla_nombre):
    anomalias = config['generation']['anomalies']
    
    if anomalias['null_values_percentage'] > 0:
        mask = np.random.rand(*df.shape) < anomalias['null_values_percentage']
        df = df.mask(mask, None)

    if 'fec_mov' in df.columns and anomalias['out_of_range_dates'] > 0:
        indices = np.random.choice(df.index, size=anomalias['out_of_range_dates'], replace=False)
        df.loc[indices, 'fec_mov'] = pd.to_datetime('2099-01-01')

    if tabla_nombre == 'TB_MOV_FINANCIEROS' and anomalias['duplicate_transactions'] > 0:
        duplicados = df.sample(n=anomalias['duplicate_transactions'])
        df = pd.concat([df, duplicados], ignore_index=True)
        
    return df

def main():
    print("Iniciando generación de datos sintéticos...")
    
    os.makedirs('data-generation/data_output/csv', exist_ok=True)
    os.makedirs('data-generation/data_output/parquet', exist_ok=True)

    connection_string = f"mssql+pyodbc://{username}:{password}@{server}/{database}?driver={driver}&TrustServerCertificate=yes"
    engine = create_engine(connection_string, fast_executemany=True)

    vol_clientes = config['generation']['tables']['TB_CLIENTES_CORE']['volume']
    vol_productos = config['generation']['tables']['TB_PRODUCTOS_CAT']['volume']
    vol_movimientos = config['generation']['tables']['TB_MOV_FINANCIEROS']['volume']
    vol_obligaciones = config['generation']['tables']['TB_OBLIGACIONES']['volume']
    vol_sucursales = config['generation']['tables']['TB_SUCURSALES_RED']['volume']
    vol_comisiones = config['generation']['tables']['TB_COMISIONES_LOG']['volume']

    print("Generando TB_CLIENTES_CORE...")
    df_clientes = generar_clientes(vol_clientes)
    
    print("Generando TB_PRODUCTOS_CAT...")
    df_productos = generar_productos(vol_productos)
    
    print("Generando TB_MOV_FINANCIEROS...")
    df_movimientos = generar_movimientos(vol_movimientos, df_clientes, df_productos)

    print("Generando TB_OBLIGACIONES...")
    df_obligaciones = generar_obligaciones(vol_obligaciones, df_clientes, df_productos)
    
    print("Generando TB_SUCURSALES_RED...")
    df_sucursales = generar_sucursales(vol_sucursales)
    
    print("Generando TB_COMISIONES_LOG...")
    df_comisiones = generar_comisiones(vol_comisiones, df_clientes, df_productos)

    tablas = {
        'TB_CLIENTES_CORE': df_clientes,
        'TB_PRODUCTOS_CAT': df_productos,
        'TB_MOV_FINANCIEROS': df_movimientos,
        'TB_OBLIGACIONES': df_obligaciones,
        'TB_SUCURSALES_RED': df_sucursales,
        'TB_COMISIONES_LOG': df_comisiones
    }

    for nombre_tabla, df in tablas.items():
        print(f"Inyectando anomalías y exportando {nombre_tabla}...")
        df_anomalo = inyectar_anomalias(df, nombre_tabla)
        
        # CSV
        df_anomalo.to_csv(f'data-generation/data_output/csv/{nombre_tabla}.csv', index=False)
        # PARQUET
        df_anomalo.to_parquet(f'data-generation/data_output/parquet/{nombre_tabla}.parquet', index=False)
        
        # Cargue a Azure SQL
        print(f"Cargando {nombre_tabla} a Azure SQL...")
        df_anomalo.to_sql(nombre_tabla, engine, if_exists='replace', index=False, chunksize=1000)

    print("¡Fase 1 completada exitosamente! Las 6 tablas han sido generadas y cargadas.")

if __name__ == "__main__":
    main()