variable "function_name" {
  type        = string
  description = "Function App Name"
}

variable "rg_location" {
  type        = string
  description = "Resource group location"
}

variable "rg_name" {
  type        = string
  description = "Resource group name"
}

variable "service_plan_id" {
  type        = string
  description = "ID of the app service plan"
}

variable "storage_name" {
  type        = string
  description = "Storage account name"
}

variable "storage_primary_access_key" {
  type        = string
  description = "Storage account primary access key"
}
