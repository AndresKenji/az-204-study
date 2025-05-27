resource "azurerm_storage_account" "this" {
  name                     = var.storage_account_name
  location                 = var.location
  resource_group_name      = var.storage_account_rg_name
  account_tier             = var.account_tier
  account_replication_type = var.account_replication_type
}

resource "azurerm_storage_management_policy" "this" {
  count              = var.enable_lifecycle_policy ? 1 : 0
  storage_account_id = azurerm_storage_account.this.id

  dynamic "rule" {
    for_each = var.lifecycle_rules
    content {
      name    = rule.value.name
      enabled = true

      filters {
        blob_types   = ["blockBlob"]
        prefix_match = [rule.value.prefix]
      }

      actions {
        base_blob {
          tier_to_cool_after_days_since_modification_greater_than = rule.value.tier_days
          delete_after_days_since_modification_greater_than      = rule.value.delete_days
        }
      }
    }
  }
}
