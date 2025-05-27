variable "rg_name" {
  type        = string
  description = "Resource group name"
}

variable "rg_location" {
  type        = string
  description = "Resource group location"
}

variable "app_service_plan_name" {
  type        = string
  description = "App Service plan name"
}

variable "sku_name" {
  type        = string
  description = "Stock Keeping Unit for the service plan"
  default     = "F1"
}

variable "os_type" {
  type        = string
  description = "Operative sistem for the service plan"
  default     = "Linux"
}
