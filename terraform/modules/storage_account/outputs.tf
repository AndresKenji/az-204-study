output "storage_account_id" {
  value       = azurerm_storage_account.this.id
  description = "ID de la cuenta de almacenamiento"
}

output "storage_account_name" {
  value       = azurerm_storage_account.this.name
  description = "Nombre del storage account"
}

output "storage_primary_access_key" {
  value       = azurerm_storage_account.this.primary_access_key
  description = "Primary acces key del storage account"
}