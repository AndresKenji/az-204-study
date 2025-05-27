resource "azurerm_resource_group" "main_rg" {
  name     = "az-204-practice-rg"
  location = var.location
}

# --- STORAGE ACCOUNT principal (con lifecycle opcional) ---
module "st_account" {
  source                  = "../../modules/storage_account"
  storage_account_name    = var.storage_account_name
  storage_account_rg_name = azurerm_resource_group.main_rg.name
  location                = var.location

  # habilitamos lifecycle y definimos reglas
  enable_lifecycle_policy = true
  lifecycle_rules = [
    {
      name        = "archive-cleanup"
      prefix      = "archive/"
      tier_days   = 30
      delete_days = 365
    },
    {
      name        = "logs-cleanup"
      prefix      = "logs/"
      tier_days   = 7
      delete_days = 30
    }
  ]

}

module "function_st_account" {
  source                  = "../../modules/storage_account"
  storage_account_name    = var.function_storage_name
  storage_account_rg_name = azurerm_resource_group.main_rg.name
  location                = var.location

  enable_lifecycle_policy = var.fn_account_enable_lifecycle_policy
  lifecycle_rules         = var.fn_account_lifecycle_rules

}

module "web_service_plan" {
  source                = "../../modules/service_plan"
  app_service_plan_name = var.app_web_service_plan_name
  rg_location           = var.location
  rg_name               = azurerm_resource_group.main_rg.name
}

module "app_service_plan" {
  source                = "../../modules/service_plan"
  app_service_plan_name = var.app_service_plan_name
  rg_location           = var.location
  rg_name               = azurerm_resource_group.main_rg.name
  sku_name              = var.function_sku
}

module "web_app" {
  source              = "../../modules/python_web_app"
  name                = var.web_app_name
  location            = var.location
  service_plan_id     = module.web_service_plan.app_service_plan_id
  resource_group_name = azurerm_resource_group.main_rg.name
}

module "function" {
  source                     = "../../modules/azure_function_app"
  storage_name               = var.function_storage_name
  rg_name                    = azurerm_resource_group.main_rg.name
  rg_location                = azurerm_resource_group.main_rg.location
  service_plan_id            = module.app_service_plan.app_service_plan_id
  storage_primary_access_key = module.function_st_account.storage_primary_access_key
  function_name              = var.function_name
}