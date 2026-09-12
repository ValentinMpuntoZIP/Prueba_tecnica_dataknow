# Changelog - Pryecto Data Engineer - DataKnow (Escenario A: Banca)

Todos los cambios notables en este proyecto serán documentados en este archivo.
El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/), y este proyecto se adhiere al Versionamiento Semántico.
## [1.4.0] - 2026-09-12
### Añadido
- **Aprovisionamiento RBAC en Terraform:** Integración real de `azurerm_role_assignment` en `main.tf` para aplicar los roles de Ingeniero de Datos (Storage Blob Data Contributor) y Analista (Storage Blob Data Reader) directamente como código sobre el Data Lake.
- **Webhook de Alertas como Código:** Creación del recurso Logic App y su respectivo trigger HTTP en Terraform para gestionar de forma funcional las alertas de fallo del pipeline en Azure Data Factory.
### Cambiado
- **Ingesta Incremental en Capa Bronze:** Refactorización de `capa_bronze.py` para incorporar el control por marcas de agua (*watermarks*), evitando cargas masivas completas y procesando únicamente registros nuevos desde la última ejecución.
- **Reubicación de Lógica de Fraude (`ind_sospechoso`):** Traslado formal del cálculo del indicador de transacciones sospechosas desde la Capa Gold hacia la Capa Silver, cumpliendo estrictamente con los lineamientos técnicos del desafío.
- **Parametrización Multi-entorno de Recursos:** Actualización de los nombres en Terraform (`Storage Account`, `Key Vault`, `Data Factory`) para soportar dinámicamente `${var.environment}` y asegurar despliegues limpios sin colisiones globales.
- **README.md** Actualizado con insertación de imágenes como evidencia.

## [1.3.0] - 2026-09-11
### Añadido
- **Gobierno de Datos y RBAC:** Creación de `gobierno_roles.md` para documentar la asignación de roles en Azure bajo el principio de mínimo privilegio (Administrador, Ingeniero de Datos, Analista).
- **Catálogo de Datos:** Creación de `catalogo_datos.md` detallando el diccionario de datos de las capas Silver y Gold, especificando tipos, orígenes y marcando los campos sensibles (PII).
- **Documentación Visual y de Ejecución:** Integración de diagramas Mermaid en `arquitectura.md` y `diagrama_er.md`. Creación del manual definitivo paso a paso en `guia_ejecucion.md`.
### Cambiado
- **README.md:** Reestructurado totalmente para incluir la justificación técnica de la selección del Escenario A (Financiero) y la elección de Azure como plataforma cloud, cumpliendo con los estándares de evaluación.

## [1.2.0] - 2026-09-10
### Añadido
- **Pruebas Automatizadas (QA):** Implementación del script `qa_tests.py` integrado al orquestador. Incluye 5 reglas de calidad automatizadas sobre la capa Gold:
  1. Unicidad de llaves primarias en dimensiones.
  2. Completitud (sin nulos) en campos críticos como documentos.
  3. Consistencia de rangos (sin saldos negativos).
  4. Integridad referencial (clientes fact_cartera vs dim_clientes).
  5. Validez matemática de reglas de negocio (CLTV positivo).

## [1.1.1] - 2026-09-09
### Añadido
- **Orquestador Local y Alertas:** Creación del script maestro `run_pipeline.py` para ejecutar el flujo secuencial completo (Bronze -> Silver -> Gold -> QA) y generar el reporte diario.
- **Detección de Anomalías de Volumen:** Integración de lógica matemática en el orquestador local para disparar alertas automáticas si la variación de ingesta supera el 30% respecto al promedio histórico.
### Cambiado
- **Orquestación en ADF:** Reestructuración de `adf_pipeline.json` para reflejar las dependencias secuenciales estrictas de la arquitectura Medallion, manteniendo las políticas de 3 reintentos (intervalo de 30s) y conectando alertas WebHook por fallos de ejecución.

## [1.1.0] - 2026-09-08
### Añadido
- **Lógica de Negocio en Capa Gold:** Desarrollo del modelo Dimensional (Star Schema) incorporando reglas de negocio complejas, cálculo de provisiones regulatorias, segmentación de buckets de mora y consolidación de Rentabilidad (CLTV).
### Cambiado
- **Manejo de Registros Huérfanos:** Implementación de validación de integridad referencial en la capa Silver. Los registros que no cruzan con dimensiones maestras son desviados a una ruta de auditoría.
### Seguridad
- **Protección PII (Enmascaramiento):** Integración de encriptación hash (SHA-256) en la capa Silver para anonimizar campos sensibles como `nomb_completo` y `num_doc` en `TB_CLIENTES_CORE`, garantizando el cumplimiento normativo.

## [1.0.1] - 2026-09-07
### Cambiado
- **Refactorización IaC (Terraform):** Parametrización del provider eliminando credenciales expuestas y `subscription_id` hardcodeado (migración a variables de entorno e inyección vía Key Vault).
- **Despliegue Multi-entorno:** Implementación de Workspaces (`dev`, `prod`) para aislar los entornos de infraestructura y cumplir con las mejores prácticas.
### Corregido
- **Conflictos de Nomenclatura Global en Azure:** Resolución de errores `409 Conflict` y `VaultAlreadyExists` añadiendo un sufijo único (`vcmg`) a los recursos *Storage Account*, *Key Vault* y *Data Factory*.
- **Estado Remoto:** Configuración correcta del backend `azurerm` en `providers.tf` apuntando al contenedor `tfstate` en el grupo de recursos de gestión (`rg-Fibank-pruebavcmg`).

## [1.0.0] - 2026-09-06
### Añadido
- **Generador de Datos Transaccionales:** Inicialización del simulador de datos sintéticos (`generate_data.py`) ajustado exactamente a las 6 tablas del modelo origen (TB_OBLIGACIONES, TB_SUCURSALES_RED, TB_COMISIONES_LOG, TB_CLIENTES_CORE, TB_PRODUCTOS_CAT, TB_MOV_FINANCIEROS) con inyección de anomalías controladas.
- **Estructura Base del Repositorio:** Definición del esqueleto del proyecto para soportar el patrón Medallion y el gobierno de datos exigido para la prueba de DataKnow.