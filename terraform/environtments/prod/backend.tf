terraform {
  backend "azurerm" {
    subscription_id      = "9a8d751e-c494-4ec2-889c-f431fa4dc067"
    resource_group_name  = "estados_terraform"
    storage_account_name = "estadosterraformkenji"
    container_name       = "states"
    key                  = "az204practice.tfstate"
  }
}