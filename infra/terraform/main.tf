terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 2.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# -----------------------------------
# Random suffix for globally-unique names
# -----------------------------------
resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}

# -----------------------------------
# Resource Group
# -----------------------------------
resource "azurerm_resource_group" "main" {
  name     = "rg-${var.project_name}-${var.environment}"
  location = var.location

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# -----------------------------------
# ADLS Gen2 Storage Account (Data Lake)
# -----------------------------------
resource "azurerm_storage_account" "datalake" {
  name                     = "st${var.project_name}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled           = true

  # Cost & security related settings
  access_tier                     = "Hot"
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"

  tags = {
    environment = var.environment
    project     = var.project_name
  }

  lifecycle {
    prevent_destroy = false
  }
}

# -----------------------------------
# Storage Management Policy (Lifecycle)
# - Example:
#   * Bronze: keep 90 days
#   * Silver: keep 365 days
#   * Gold: no automatic deletion (for analytics)
# -----------------------------------
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.datalake.id

  # Bronze layer: raw ingestion, short retention
  rule {
    name    = "bronze-retention"
    enabled = true

    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["bronze/weather/"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 90
      }
    }
  }

  # Silver layer: cleaned/conformed, longer retention
  rule {
    name    = "silver-retention"
    enabled = true

    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["silver/weather/"]
    }

    actions {
      base_blob {
        delete_after_days_since_modification_greater_than = 365
      }
    }
  }

  # Gold layer: analytics / reporting
  # No delete rule here – assume long-term value.
}

# -----------------------------------
# ADLS Gen2 Filesystem (Container)
# -----------------------------------
resource "azurerm_storage_data_lake_gen2_filesystem" "main" {
  name               = "environmental-data"
  storage_account_id = azurerm_storage_account.datalake.id
}

# -----------------------------------
# Azure Container Registry for Pipeline Images
# -----------------------------------
resource "azurerm_container_registry" "main" {
  name                = "acr${var.project_name}${random_string.suffix.result}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = true

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}
# -----------------------------------
# ADLS Gen2 Directories (Medallion: Bronze/Silver/Gold)
# -----------------------------------
locals {
  adls_directories = [
    "landing",           # New files landing zone
    "raw",              # Processed raw files
    "bronze/weather",
    "silver/weather",
    "gold/weather",
    "code",             # For pipeline code artifacts
  ]
}

resource "azurerm_storage_data_lake_gen2_path" "data_layers" {
  for_each           = toset(local.adls_directories)
  path               = each.value
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.main.name
  storage_account_id = azurerm_storage_account.datalake.id
  resource           = "directory"

  depends_on = [
    azurerm_storage_data_lake_gen2_filesystem.main
  ]
}

# -----------------------------------
# Synapse Workspace (Serverless-focused)
# -----------------------------------
resource "azurerm_synapse_workspace" "main" {
  name                                 = "syn-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name                  = azurerm_resource_group.main.name
  location                             = azurerm_resource_group.main.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.main.id
  sql_administrator_login              = var.sql_admin_username
  sql_administrator_login_password     = var.sql_admin_password

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# -----------------------------------
# RBAC: Synapse Workspace MI -> Storage Blob Data Contributor
# -----------------------------------
resource "azurerm_role_assignment" "synapse_storage_blob_contributor" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_synapse_workspace.main.identity[0].principal_id
}

# -----------------------------------
# Synapse Firewall Rules
# -----------------------------------

# -----------------------------------
# RBAC: ACR -> Storage Blob Data Contributor
# -----------------------------------
resource "azurerm_role_assignment" "acr_storage_contributor" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_container_registry.main.identity[0].principal_id
}

# -----------------------------------
# Service Principal for Pipeline Access
# -----------------------------------
data "azuread_client_config" "current" {}

resource "azuread_application" "pipeline_app" {
  display_name = "sp-environmental-pipeline"
  owners       = [data.azuread_client_config.current.object_id]
}

resource "azuread_service_principal" "pipeline_sp" {
  client_id = azuread_application.pipeline_app.client_id
  owners    = [data.azuread_client_config.current.object_id]
}

resource "azuread_service_principal_password" "pipeline_sp_password" {
  service_principal_id = azuread_service_principal.pipeline_sp.object_id
}

# Grant service principal access to storage
resource "azurerm_role_assignment" "pipeline_sp_storage" {
  scope                = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azuread_service_principal.pipeline_sp.object_id
}

resource "azurerm_synapse_firewall_rule" "allow_all_azure_services" {
  name                 = "AllowAllWindowsAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

# -----------------------------------
# Data Factory Linked Services
# -----------------------------------
resource "azurerm_data_factory_linked_service_azure_blob_storage" "code_storage_linked_service" {
  name            = "CodeStorageLinkedService"
  data_factory_id = azurerm_data_factory.main.id
  connection_string = azurerm_storage_account.datalake.primary_connection_string
}

resource "azurerm_data_factory_linked_service_azure_blob_storage" "data_lake_linked_service" {
  name            = "DataLakeLinkedService"
  data_factory_id = azurerm_data_factory.main.id
  connection_string = azurerm_storage_account.datalake.primary_connection_string
}

# -----------------------------------
# Data Factory Datasets
# -----------------------------------
resource "azurerm_data_factory_dataset_delimited_text" "landing_csv" {
  name            = "LandingCSVDataset"
  data_factory_id = azurerm_data_factory.main.id
  linked_service_name = azurerm_data_factory_linked_service_azure_blob_storage.data_lake_linked_service.name

  azure_blob_storage_location {
    container = "environmental-data"
    path      = "landing"
    filename  = "*.csv"
  }

  column_delimiter = ","
  first_row_as_header = true
}

resource "azurerm_data_factory_dataset_parquet" "bronze_parquet" {
  name            = "BronzeParquetDataset"
  data_factory_id = azurerm_data_factory.main.id
  linked_service_name = azurerm_data_factory_linked_service_azure_blob_storage.data_lake_linked_service.name

  azure_blob_storage_location {
    container = "environmental-data"
    path      = "bronze/weather"
  }
}

# -----------------------------------
# Data Factory Pipeline with Copy Activity
# -----------------------------------
resource "azurerm_data_factory_pipeline" "ingestion_pipeline" {
  name            = "EnvironmentalDataIngestionPipeline"
  data_factory_id = azurerm_data_factory.main.id
  description     = "Automated ingestion from landing to bronze layer"

  activities_json = jsonencode([
    {
      name = "CopyLandingToBronze"
      type = "Copy"
      description = "Copy CSV files from landing to bronze layer as Parquet"
      inputs = [
        {
          referenceName = azurerm_data_factory_dataset_delimited_text.landing_csv.name
          type = "DatasetReference"
        }
      ]
      outputs = [
        {
          referenceName = azurerm_data_factory_dataset_parquet.bronze_parquet.name
          type = "DatasetReference"
        }
      ]
      typeProperties = {
        source = {
          type = "DelimitedTextSource"
          storeSettings = {
            type = "AzureBlobStorageReadSettings"
            recursive = true
            wildcardFileName = "*.csv"
          }
        }
        sink = {
          type = "ParquetSink"
          storeSettings = {
            type = "AzureBlobStorageWriteSettings"
          }
        }
        enableStaging = false
      }
    }
  ])
}

# -----------------------------------
# Data Factory Trigger for Blob Events
# -----------------------------------
resource "azurerm_data_factory_trigger_blob_event" "landing_trigger" {
  name            = "LandingFolderTrigger"
  data_factory_id = azurerm_data_factory.main.id
  storage_account_id = azurerm_storage_account.datalake.id
  
  events = ["Microsoft.Storage.BlobCreated"]
  blob_path_begins_with = "/blobServices/default/containers/environmental-data/blobs/landing/"
  blob_path_ends_with = ".csv"
  
  activated = true
  
  pipeline {
    name = azurerm_data_factory_pipeline.ingestion_pipeline.name
  }
}
