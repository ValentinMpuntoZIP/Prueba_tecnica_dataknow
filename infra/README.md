# IaC - TERRAFORM

Este directorio contiene las plantillas de Terraform para aprovisionar los recursos de Microsoft Azure.

## Recursos Creados
* **Resource Group:** `rg-Fibank-pruebavcmg`
* **Storage Account (ADLS Gen2):** `stfinbank001vcmg` con contenedores `bronze`, `silver` y `gold`.
* **Data Factory:** Instancia de orquestación para pipelines.

## Instrucciones de Despliegue

```bash
# 1. Inicializar Terraform
terraform init

# 2. Validar plan de ejecución
terraform plan -var-file="terraform.tfvars"

# 3. Aplicar infraestructura
terraform apply -var-file="terraform.tfvars" -auto-approve
```