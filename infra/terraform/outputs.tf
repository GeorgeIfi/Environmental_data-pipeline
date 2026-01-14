output "storage_account_name" {
  value = azurerm_storage_account.datalake.name
}

output "synapse_workspace_name" {
  value = azurerm_synapse_workspace.main.name
}

output "synapse_sql_endpoint" {
  value = azurerm_synapse_workspace.main.connectivity_endpoints.sql
}

output "data_factory_name" {
  value = azurerm_data_factory.main.name
}

output "container_registry_name" {
  value = azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "service_principal_app_id" {
  value = azuread_application.pipeline_app.client_id
}

output "service_principal_password" {
  value     = azuread_service_principal_password.pipeline_sp_password.value
  sensitive = true
}

output "storage_account_key" {
  value     = azurerm_storage_account.datalake.primary_access_key
  sensitive = true
}