variable "environment" {
  description = "Entorno de despliegue (ej. dev, prod)"
  type        = string
}

variable "location" {
  description = "Región de Azure"
  type        = string
  default     = "East US"
}

variable "admin_email" {
  description = "Correo para alertas de Action Group"
  type        = string
  default     = "alertas@finbank.com"
}