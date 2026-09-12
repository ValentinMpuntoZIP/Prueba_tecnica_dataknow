data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "rg" {
  name     = "rg-finbank-${var.environment}"
  location = var.location
}

#ADLS gen2
resource "azurerm_storage_account" "datalake" {
  name                     = "stfinbank${var.environment}vcmg"
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true
}

resource "azurerm_storage_data_lake_gen2_filesystem" "layers" {
  for_each           = toset(["bronze", "silver", "gold"])
  name               = each.key
  storage_account_id = azurerm_storage_account.datalake.id
}

# Azure key Vault
resource "azurerm_key_vault" "kv" {
  name                       = "kv-finbank-${var.environment}-vcmg"
  location                   = azurerm_resource_group.rg.location
  resource_group_name        = azurerm_resource_group.rg.name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
}

# adf
resource "azurerm_data_factory" "adf" {
  name                = "adf-finbank-dev-vcmg"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}
# Log's
resource "azurerm_log_analytics_workspace" "law" {
  name                = "law-finbank-${var.environment}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

#Alertas
resource "azurerm_monitor_action_group" "alerts" {
  name                = "ag-finbank-${var.environment}"
  resource_group_name = azurerm_resource_group.rg.name
  short_name          = "ag-alerts"

  email_receiver {
    name                    = "Admin_Alerts"
    email_address           = var.admin_email
    use_common_alert_schema = true
  }
}

# Creación de Logic App para recibir la alerta de ADF
resource "azurerm_logic_app_workflow" "alertas" {
  name                = "logic-alertas-finbank-${var.environment}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
}

resource "azurerm_logic_app_trigger_http_request" "webhook" {
  name         = "webhook-trigger"
  logic_app_id = azurerm_logic_app_workflow.alertas.id
  schema       = <<SCHEMA
  {
    "type": "object",
    "properties": {
      "message": { "type": "string" }
    }
  }
  SCHEMA
}

# Roles y permisos RBAC
# Rol Ingeniero de Datos (Lectura y Escritura sobre todo el Data Lake)
resource "azurerm_role_assignment" "data_engineer" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Rol Analista (Solo lectura, restringido al contenedor Gold)
resource "azurerm_role_assignment" "data_analyst" {
  scope                = "${azurerm_storage_account.datalake.id}/blobServices/default/containers/gold"
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = data.azurerm_client_config.current.object_id
}