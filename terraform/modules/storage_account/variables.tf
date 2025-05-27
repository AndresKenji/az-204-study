variable "storage_account_name" {
  type        = string
  description = "Nombre de la cuenta de almacenamiento"
}

variable "storage_account_rg_name" {
  type        = string
  description = "Nombre del grupo de recursos donde se creará la cuenta de almacenamiento"
}

variable "location" {
  type        = string
  description = "Ubicación donde se creará la cuenta de almacenamiento"
}

variable "account_tier" {
  type        = string
  description = "Valores: Standard o Premium"
  default     = "Standard"
}

variable "account_replication_type" {
  type        = string
  description = "Tipo de replicación valores: LRS, GRS, RA-GRS, ZRS, GZRS, RA-GZRS"
  default     = "LRS"
}


variable "lifecycle_rules" {
  description = "Reglas de ciclo de vida para blobs"
  type = list(object({
    name        = string
    prefix      = string
    tier_days   = number
    delete_days = number
  }))
  default = []
}

variable "enable_lifecycle_policy" {
  description = "Habilita la política de ciclo de vida"
  type        = bool
  default     = false
}