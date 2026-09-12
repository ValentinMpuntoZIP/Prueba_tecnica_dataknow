# Catálogo de Datos - FinBank (Escenario A)

> **Nota de Seguridad y Cumplimiento:** Los campos marcados como `[Sensible: SÍ]` contienen Información Personal Identificable (PII). Según las políticas de gobierno de datos, estos campos viajan con enmascaramiento estático o cifrado hash (SHA-256) desde la capa Silver para proteger la identidad del cliente.

---

## 1. Capa Silver (Datos Conformados y Seguros)
Contiene las réplicas exactas de las fuentes transaccionales tras pasar por procesos de limpieza de nulos, deduplicación, validación de integridad referencial y enmascaramiento de seguridad.

### 1.1. TB_CLIENTES_CORE_silver
Dimensión maestra de clientes con datos personales protegidos.
| Campo | Tipo de Dato | Origen | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_cli` | Integer | TB_CLIENTES_CORE | Identificador único del cliente | No |
| `nomb_cli` | String | TB_CLIENTES_CORE | Nombre del cliente (Enmascarado) | **SÍ** |
| `apell_cli` | String | TB_CLIENTES_CORE | Apellido del cliente (Enmascarado) | **SÍ** |
| `tip_doc` | String | TB_CLIENTES_CORE | Tipo de documento de identidad | No |
| `num_doc` | String | TB_CLIENTES_CORE | Número de documento (Aplicado Hash SHA-256) | **SÍ** |
| `fec_nac` | Date | TB_CLIENTES_CORE | Fecha de nacimiento | No |
| `cod_segmento` | String | TB_CLIENTES_CORE | Categoría de ingresos del cliente | No |
| `ciudad_res` | String | TB_CLIENTES_CORE | Ciudad de residencia | No |

### 1.2. TB_MOV_FINANCIEROS_silver
Registro transaccional validado mediante integridad referencial (FK).
| Campo | Tipo de Dato | Origen | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_mov` | Integer | TB_MOV_FINANCIEROS | Identificador de la transacción | No |
| `id_cli` | Integer | TB_MOV_FINANCIEROS | Llave foránea del cliente (Validada) | No |
| `cod_prod` | String | TB_MOV_FINANCIEROS | Llave foránea del producto (Validada) | No |
| `fec_mov` | Date | TB_MOV_FINANCIEROS | Fecha de la transacción | No |
| `vr_mov` | Float | TB_MOV_FINANCIEROS | Valor monetario en COP | No |
| `tip_mov` | String | TB_MOV_FINANCIEROS | Tipo de movimiento (Pago, Retiro, etc.) | No |

*(Nota: Las tablas `TB_PRODUCTOS_CAT`, `TB_SUCURSALES_RED`, `TB_OBLIGACIONES` y `TB_COMISIONES_LOG` en Silver mantienen su estructura original de Bronze, garantizando el cruce relacional).*

---

## 2. Capa Gold (Capa Analítica y de Negocio)
Contiene el modelo de estrella (Star Schema) optimizado para consumo, reportes regulatorios y modelos de machine learning.

### 2.1. Dimensiones (DIM)

**dim_clientes**
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_cli` | Integer | TB_CLIENTES_CORE | Llave primaria | No |
| `nomb_completo` | String | Concatenación Nombre + Apellido | Nombre consolidado (Enmascarado) | **SÍ** |
| `num_doc` | String | TB_CLIENTES_CORE | Documento unificado (Hash SHA-256) | **SÍ** |
| `edad` | Integer | Calculado desde `fec_nac` | Edad calculada en años al corte | No |
| `desc_segmento` | String | Estandarizado a MAYÚSCULAS | Segmento comercial | No |

**dim_productos**
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `cod_prod` | String | TB_PRODUCTOS_CAT | Llave primaria del producto | No |
| `familia_prod` | String | Agrupado desde `tip_prod` | Clasificación macro del producto | No |
| `tasa_mensual` | Float | Derivado de `tasa_ea` | Equivalencia de tasa de interés mensual | No |

### 2.2. Tablas de Hechos (FACT) y KPIs

**fact_cartera**
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_oblig` | Integer | TB_OBLIGACIONES | Llave primaria de la obligación | No |
| `sdo_capital` | Float | TB_OBLIGACIONES | Saldo actual de la deuda | No |
| `bucket_mora` | String | Calculado s/ `dias_mora_act` | Clasificación de mora en 5 rangos de negocio | No |
| `provision_estimada`| Float | Calculado s/ `calif_riesgo` | Provisión regulatoria exigida en valor | No |

**fact_transacciones**
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_mov` | Integer | TB_MOV_FINANCIEROS | Identificador de transacción | No |
| `vr_mov_usd` | Float | Conversión desde COP | Valor transado en USD | No |
| `ind_sospechoso` | Integer (0/1) | Umbral estadístico (Media + 3xStd) | Flag de transacción atípica (Prevención Fraude) | No |

**fact_rentabilidad_cliente (CLTV)**
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `id_cli` | Integer | Llave dimensional | ID del cliente | No |
| `ingreso_intereses`| Float | Cálculo sobre saldos 12 meses | Ingreso proyectado por créditos | No |
| `vr_comision` | Float | Suma comisiones cobradas 12m | Ingreso por transaccionalidad | No |
| `cltv_total` | Float | Intereses + Comisiones | Customer Lifetime Value consolidado | No |

**kpis_diarios_cartera**
Consolidado gerencial diario, granularidad por fecha, producto, segmento y ciudad.
| Campo | Tipo de Dato | Origen / Transformación | Descripción | Sensible (PII) |
| :--- | :--- | :--- | :--- | :--- |
| `fecha_corte` | Date | Snapshot de ejecución | Fecha de agregación del KPI | No |
| `monto_en_mora` | Float | Suma `sdo_capital` en mora | Saldo en riesgo total | No |
| `tasa_mora_pct` | Float | (Mora / Cartera Total) * 100 | Porcentaje general de deterioro | No |