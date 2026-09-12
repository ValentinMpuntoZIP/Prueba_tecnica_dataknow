# Arquitectura de la Solución (Medallón)

El proyecto implementa un pipeline completo desplegado y orquestado en Microsoft Azure.

```mermaid
graph LR
    A[(Azure SQL)] -->|Ingesta Parquet| B(Capa Bronze)
    B -->|Limpieza y Enmascaramiento| C(Capa Silver)
    C -->|Reglas de Negocio| D(Capa Gold)
    
    subgraph Orquestacion y Seguridad
    B
    C
    D
    end
    
    E[Azure Key Vault] -.-> A
    F[Terraform] -.->|Aprovisiona| B