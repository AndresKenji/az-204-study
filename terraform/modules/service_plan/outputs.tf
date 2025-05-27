output "app_service_plan_name" {
  description = "Name of the App Service"
  value       = azurerm_service_plan.service_plan.name
}

output "app_service_plan_id" {
  description = "ID of the Azure Service Plan"
  value       = azurerm_service_plan.service_plan.id
}





