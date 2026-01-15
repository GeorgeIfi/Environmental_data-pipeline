resource "azurerm_data_factory" "main" {
  name                = "adf-environmental-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "main" {
  name                = "ls-datalake"
  resource_group_name = azurerm_resource_group.main.name
  data_factory_name   = azurerm_data_factory.main.name
  url                 = azurerm_storage_account.datalake.primary_dfs_endpoint
  use_managed_identity = true
}

# ADF pipeline for environmental data processing
# (Replaced by orchestration_pipeline with Azure Functions in main.tf)

# ADF trigger for daily execution
# (Replaced by Azure Functions orchestration in main.tf)

resource "azurerm_role_assignment" "adf_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}