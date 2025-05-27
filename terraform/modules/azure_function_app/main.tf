resource "azurerm_linux_function_app" "azure_function" {
  name                = var.function_name
  resource_group_name = var.rg_name
  location            = var.rg_location

  storage_account_name       = var.storage_name
  storage_account_access_key = var.storage_primary_access_key

  service_plan_id = var.service_plan_id

  site_config {}
}