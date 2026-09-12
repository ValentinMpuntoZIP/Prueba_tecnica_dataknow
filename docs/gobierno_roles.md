# Políticas de Gobierno, Roles y Accesos (RBAC)

Este documento define la estrategia de seguridad y control de acceso implementada en Azure para el proyecto FinBank, garantizando el principio de mínimo privilegio sobre el Data Lake (ADLS Gen2).

## 1. Perfiles y Asignación de Roles en Azure (IAM)

### A. Administrador (Control Total)
* **Descripción:** Responsable de la infraestructura cloud, redes, facturación y gestión de identidades.
* **Rol Asignado:** `Owner` (Propietario) o `Contributor` a nivel de Resource Group (`rg-finbank-dev`).
* **Alcance:** Capacidad para desplegar infraestructura vía Terraform, gestionar Azure Key Vault, Log Analytics y Azure Data Factory.

### B. Ingeniero de Datos (Lectura y Escritura Total)
* **Descripción:** Perfil técnico encargado de la orquestación y transformación de datos en todo el pipeline Medallion.
* **Rol Asignado:** `Storage Blob Data Contributor`.
* **Alcance:** Acceso de lectura, escritura y borrado asignado a nivel del Storage Account (`stfinbankdevvcmg`). Puede interactuar libremente con los contenedores `bronze`, `silver` y `gold`.

### C. Analista (Solo Lectura Analítica)
* **Descripción:** Científico de datos o analista de BI que consume los tableros y modelos finales.
* **Rol Asignado:** `Storage Blob Data Reader` asignado **exclusivamente a nivel del contenedor `gold`**.
* **Alcance:** Solo puede leer e inferir datos sobre el modelo de estrella en la capa Gold. 
* **Evidencia de Acceso Denegado:** Al intentar listar o consultar los contenedores `bronze` o `silver` (donde residen datos no estructurados o PII sin enmascarar), el sistema de Azure deniega la petición con un error `403 AuthorizationPermissionMismatch`.

## 2. Gestión de Secretos
Ninguna credencial de base de datos o llave de almacenamiento está expuesta en el código. Todos los secretos se inyectan a través de variables de entorno locales (durante desarrollo) y están diseñados para ser centralizados en **Azure Key Vault** (`kv-finbank-dev-vcmg`) para los pipelines en producción.