resource "azurerm_data_factory" "main" {
  name                = "adf-environmental-${random_string.suffix.result}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_data_factory_linked_service_data_lake_storage_gen2" "main" {
  name                 = "ls-datalake"
  data_factory_id      = azurerm_data_factory.main.id
  url                  = azurerm_storage_account.datalake.primary_dfs_endpoint
  use_managed_identity = true
}

# ADF pipeline for environmental data processing
resource "azurerm_data_factory_pipeline" "environmental_pipeline" {
  name            = "environmental-data-pipeline"
  data_factory_id = azurerm_data_factory.main.id
  description     = "Medallion architecture pipeline for environmental data"

  activities_json = jsonencode([
    {
      name = "IngestToBronze"
      type = "Copy"
      description = "Ingest raw CSV to Bronze layer"
      typeProperties = {
        source = {
          type = "DelimitedTextSource"
        }
        sink = {
          type = "ParquetSink"
        }
      }
    }
  ])
}

# ADF trigger for daily execution
resource "azurerm_data_factory_trigger_schedule" "daily_trigger" {
  name            = "daily-environmental-trigger"
  data_factory_id = azurerm_data_factory.main.id
  pipeline_name   = azurerm_data_factory_pipeline.environmental_pipeline.name
  
  frequency = "Day"
  interval  = 1
  
  schedule {
    hours   = [0]
    minutes = [0]
  }
}

resource "azurerm_role_assignment" "adf_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.main.identity[0].principal_id
}