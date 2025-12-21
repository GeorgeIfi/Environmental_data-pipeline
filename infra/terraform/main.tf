terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~>3.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "main" {
  name     = "rg-environmental-pipeline"
  location = var.location
}

resource "azurerm_storage_account" "datalake" {
  name                     = "stenvdata${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.main.name
  location                = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  is_hns_enabled          = true
}

resource "azurerm_storage_data_lake_gen2_filesystem" "main" {
  name               = "environmental-data"
  storage_account_id = azurerm_storage_account.datalake.id
}

resource "azurerm_synapse_workspace" "main" {
  name                                 = "synapse-environmental-${random_string.suffix.result}"
  resource_group_name                  = azurerm_resource_group.main.name
  location                            = azurerm_resource_group.main.location
  storage_data_lake_gen2_filesystem_id = azurerm_storage_data_lake_gen2_filesystem.main.id
  sql_administrator_login              = var.sql_admin_username
  sql_administrator_login_password     = var.sql_admin_password

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_synapse_sql_pool" "main" {
  name                 = "environmentalpool"
  synapse_workspace_id = azurerm_synapse_workspace.main.id
  sku_name            = "DW100c"
  create_mode         = "Default"
}

resource "random_string" "suffix" {
  length  = 8
  special = false
  upper   = false
}