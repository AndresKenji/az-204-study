output "app_function_name" {
  description = "Name of the Azure Function App"
  value       = azurerm_linux_function_app.azure_function.name
}

output "possible_outbound_ip_addresses" {
  description = "Possible given ip address for the Azure Function Application"
  value       = azurerm_linux_function_app.azure_function.possible_outbound_ip_addresses
}

output "default_hostname" {
  description = "Expected URL for the Azure Function"
  value       = azurerm_linux_function_app.azure_function.default_hostname
}

output "id" {
  description = "ID of the Azure Function Application"
  value       = azurerm_linux_function_app.azure_function.id
}