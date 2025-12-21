output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.main.name
}

output "synapse_sql_endpoint" {
  value = azurerm_synapse_workspace.main.connectivity_endpoints.sql
}

output "storage_account_key" {
  value     = azurerm_storage_account.datalake.primary_access_key
  sensitive = true
}