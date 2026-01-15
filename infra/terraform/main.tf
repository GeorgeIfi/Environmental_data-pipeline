terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 2.99"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

provider "azurerm" {
  features {}
  
  subscription_id = var.subscription_id
  tenant_id       = var.tenant_id
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
  access_tier             = "Hot"
  min_tls_version         = "TLS1_2"

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
# NOTE: Storage Management Policy disabled due to Azure requirements
# Must enable "Track Last Access Time" on storage account first
# -----------------------------------
# resource "azurerm_storage_management_policy" "lifecycle" {
#   storage_account_id = azurerm_storage_account.datalake.id
# 
#   # Bronze layer: raw ingestion, short retention
#   rule {
#     name    = "bronze-retention"
#     enabled = true
# 
#     filters {
#       blob_types   = ["blockBlob"]
#       prefix_match = ["bronze/weather/"]
#     }
# 
#     actions {
#       base_blob {
#         delete_after_days_since_modification_greater_than = 90
#       }
#     }
#   }
# 
#   # Silver layer: cleaned/conformed, longer retention
#   rule {
#     name    = "silver-retention"
#     enabled = true
# 
#     filters {
#       blob_types   = ["blockBlob"]
#       prefix_match = ["silver/weather/"]
#     }
# 
#     actions {
#       base_blob {
#         delete_after_days_since_modification_greater_than = 365
#       }
#     }
#   }
# 
#   # Gold layer: analytics / reporting
#   # No delete rule here – assume long-term value.
# }

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
# Synapse Workspace (SQL-focused)
# NOTE: Spark pool removed - using pandas for transformations
# -----------------------------------
resource "azurerm_synapse_workspace" "main" {
  name                                 = "syn-${var.project_name}-${var.environment}-${random_string.suffix.result}"
  resource_group_name                  = azurerm_resource_group.main.name
  location                             = azurerm_resource_group.main.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.main.id
  sql_administrator_login              = var.sql_admin_username
  sql_administrator_login_password     = var.sql_admin_password

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# -----------------------------------
# Note: Spark Pool removed (using pandas instead of Spark)
# Synapse workspace is available for SQL analytics queries
# -----------------------------------

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
# Use existing service principal created via Azure CLI
# Note: Reference via principal_id directly since we don't have azuread provider

# Grant service principal access to storage using the app ID mapped to principal
# The principal_id is looked up by Azure automatically from the app ID
resource "azurerm_role_assignment" "pipeline_sp_storage" {
  scope              = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id       = "5abc89eb-e289-4e27-98ca-385ed3795593"  # Service Principal object ID
}

resource "azurerm_synapse_firewall_rule" "allow_all_azure_services" {
  name                 = "AllowAllWindowsAzureIps"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  start_ip_address     = "0.0.0.0"
  end_ip_address       = "0.0.0.0"
}

# -----------------------------------
# Data Factory Linked Services
# (Data Lake linked service defined in data_factory.tf)
# -----------------------------------

# -----------------------------------
# Data Factory Datasets
# (Handled by Azure Functions transformations)
# -----------------------------------

# -----------------------------------
# Data Factory Pipeline with Copy Activity
# (Replaced by Azure Functions orchestration)
# -----------------------------------

# -----------------------------------
# Data Factory Trigger for Blob Events
# (Replaced by Azure Functions orchestration)
# -----------------------------------

# -----------------------------------
# Azure Functions Infrastructure
# - 3 HTTP-triggered functions for medallion ETL
# - Orchestrated by Data Factory
# -----------------------------------

# App Service Plan (Consumption tier for cost efficiency)
resource "azurerm_app_service_plan" "functions" {
  name                = "asp-${var.project_name}-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  kind                = "FunctionApp"
  reserved            = true

  sku {
    tier = "Dynamic"
    size = "Y1"
  }

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "functions"
  }
}

# Storage Account for Function App runtime
resource "azurerm_storage_account" "function_storage" {
  name                     = "stfunc${var.project_name}${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "functions"
  }
}

# Function App Identity (Managed Identity for secure auth)
resource "azurerm_user_assigned_identity" "function_identity" {
  name                = "id-${var.project_name}-functions"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# RBAC: Grant Function Identity access to Data Lake Storage
resource "azurerm_role_assignment" "function_storage_contributor" {
  scope              = azurerm_storage_account.datalake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id       = azurerm_user_assigned_identity.function_identity.principal_id
}

# Function App
resource "azurerm_function_app" "etl_functions" {
  name                       = "func-${var.project_name}-${random_string.suffix.result}"
  location                   = azurerm_resource_group.main.location
  resource_group_name        = azurerm_resource_group.main.name
  app_service_plan_id        = azurerm_app_service_plan.functions.id
  storage_account_name       = azurerm_storage_account.function_storage.name
  storage_account_access_key = azurerm_storage_account.function_storage.primary_access_key
  version                    = "~4"

  identity {
    type         = "UserAssigned"
    identity_ids = [azurerm_user_assigned_identity.function_identity.id]
  }

  app_settings = {
    FUNCTIONS_WORKER_RUNTIME                = "python"
    FUNCTIONS_WORKER_RUNTIME_VERSION        = "3.10"
    AzureWebJobsStorage                     = azurerm_storage_account.function_storage.primary_blob_connection_string
    WEBSITE_RUN_FROM_PACKAGE                = "1"
    APPINSIGHTS_INSTRUMENTATIONKEY          = azurerm_application_insights.functions.instrumentation_key
    APPLICATIONINSIGHTS_CONNECTION_STRING   = azurerm_application_insights.functions.connection_string
    
    # Data Lake Storage connection
    DATA_LAKE_STORAGE_ACCOUNT_NAME          = azurerm_storage_account.datalake.name
    DATA_LAKE_STORAGE_ACCOUNT_KEY           = azurerm_storage_account.datalake.primary_access_key
    DATA_LAKE_CONTAINER_NAME                = "environmental-data"
  }

  depends_on = [
    azurerm_role_assignment.function_storage_contributor
  ]

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "functions"
  }
}

# Application Insights for Function monitoring
resource "azurerm_application_insights" "functions" {
  name                = "appins-${var.project_name}-functions"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  application_type    = "web"

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "functions"
  }
}

# Data Factory Linked Service for Azure Functions
resource "azurerm_data_factory_linked_service_web" "function_service" {
  name                     = "ls_azure_functions"
  data_factory_id          = azurerm_data_factory.main.id
  resource_group_name      = azurerm_resource_group.main.name
  authentication_type      = "Anonymous"
  url                      = "https://${azurerm_function_app.etl_functions.default_hostname}"
}

# Data Factory Pipeline for orchestrating Azure Functions
resource "azurerm_data_factory_pipeline" "orchestration_pipeline" {
  name                = "OrchestrationPipeline"
  data_factory_id     = azurerm_data_factory.main.id
  resource_group_name = azurerm_resource_group.main.name

  activities_json = jsonencode([
    {
      name = "BronzeIngestActivity"
      type = "WebActivity"
      typeProperties = {
        method = "POST"
        url    = "https://${azurerm_function_app.etl_functions.default_hostname}/api/bronze-ingest"
        headers = {
          "Content-Type" = "application/json"
        }
        body = {
          storage_account = azurerm_storage_account.datalake.name
          storage_key     = azurerm_storage_account.datalake.primary_access_key
          container       = "environmental-data"
          csv_file        = "landing/weather_raw.csv"
        }
        authentication = {
          type = "Anonymous"
        }
      }
      dependsOn = []
    },
    {
      name = "SilverTransformActivity"
      type = "WebActivity"
      typeProperties = {
        method = "POST"
        url    = "https://${azurerm_function_app.etl_functions.default_hostname}/api/silver-transform"
        headers = {
          "Content-Type" = "application/json"
        }
        body = {
          storage_account = azurerm_storage_account.datalake.name
          storage_key     = azurerm_storage_account.datalake.primary_access_key
          container       = "environmental-data"
          bronze_file     = "bronze/raw_data.parquet"
        }
        authentication = {
          type = "Anonymous"
        }
      }
      dependsOn = [
        {
          activity = "BronzeIngestActivity"
          dependencyConditions = ["Succeeded"]
        }
      ]
    },
    {
      name = "GoldTransformActivity"
      type = "WebActivity"
      typeProperties = {
        method = "POST"
        url    = "https://${azurerm_function_app.etl_functions.default_hostname}/api/gold-transform"
        headers = {
          "Content-Type" = "application/json"
        }
        body = {
          storage_account = azurerm_storage_account.datalake.name
          storage_key     = azurerm_storage_account.datalake.primary_access_key
          container       = "environmental-data"
          silver_file     = "silver/cleaned_data.parquet"
        }
        authentication = {
          type = "Anonymous"
        }
      }
      dependsOn = [
        {
          activity = "SilverTransformActivity"
          dependencyConditions = ["Succeeded"]
        }
      ]
    }
  ])
}
