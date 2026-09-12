# Diagrama Entidad-Relación - Mod.Estrella.

El modelo analítico para el Escenario A (Finbak) se estructura en un esquema de estrella optimizado para el cálculo de mora, prevención de fraude y rentabilidad (CLTV).

```mermaid
erDiagram
    %% Relaciones
    DIM_CLIENTES ||--o{ FACT_CARTERA : "tiene"
    DIM_PRODUCTOS ||--o{ FACT_CARTERA : "asociado_a"
    DIM_CLIENTES ||--o{ FACT_TRANSACCIONES : "realiza"
    DIM_PRODUCTOS ||--o{ FACT_TRANSACCIONES : "involucra"
    DIM_CLIENTES ||--|| FACT_RENTABILIDAD_CLIENTE : "calcula_cltv"

    %% Dimensiones
    DIM_CLIENTES {
        int id_cli PK
        string nomb_completo
        string num_doc
        int edad
        string desc_segmento
        string ciudad_res
    }
    DIM_PRODUCTOS {
        string cod_prod PK
        string desc_prod
        string familia_prod
        float tasa_ea
        float tasa_mensual
    }
    
    %% Tablas de Hechos
    FACT_CARTERA {
        int id_oblig PK
        int id_cli FK
        string cod_prod FK
        float sdo_capital
        string bucket_mora
        float provision_estimada
    }
    FACT_TRANSACCIONES {
        int id_mov PK
        int id_cli FK
        string cod_prod FK
        float vr_mov_usd
        int es_habil
        int ind_sospechoso
    }
    FACT_RENTABILIDAD_CLIENTE {
        int id_cli PK
        float ingreso_intereses
        float vr_comision
        float cltv_total
    }