variable "subscription_id" {
  type        = string
  description = "Valor del id de tu subscription"
}

variable "location" {
  type        = string
  description = "Ubicación donde se creará la cuenta de almacenamiento"
}

variable "storage_account_name" {
  type        = string
  description = "Nombre de la cuenta de almacenamiento"
}

variable "app_service_plan_name" {
  type        = string
  description = "App Service plan name"
}

variable "app_web_service_plan_name" {
  type        = string
  description = "App Service plan name"
}

variable "web_app_name" {
  type        = string
  description = "Nombre de la webapp"
}

variable "function_storage_name" {
  type        = string
  description = "Nombre del storage account de la function"
}

variable "function_name" {
  type        = string
  description = "Nombre de la función"
}

variable "function_sku" {
  type = string
}

variable "main_st_account_enable_lifecycle_policy" {
  description = "¿Aplicar lifecycle policy al storage account principal?"
  type        = bool
  default     = false
}

variable "main_st_account_lifecycle_rules" {
  description = "Listado de reglas de ciclo de vida para el storage account principal"
  type = list(object({
    name        = string
    prefix      = string
    tier_days   = number
    delete_days = number
  }))
  default = []
}

variable "fn_account_enable_lifecycle_policy" {
  description = "¿Aplicar lifecycle policy al storage account de functions?"
  type        = bool
  default     = false
}

variable "fn_account_lifecycle_rules" {
  description = "Listado de reglas de ciclo de vida para el storage account de functions"
  type = list(object({
    name        = string
    prefix      = string
    tier_days   = number
    delete_days = number
  }))
  default = []
}