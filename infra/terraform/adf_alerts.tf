# ============================================================================
# Azure Data Factory: Failure Handling & Alerts
# Production-ready monitoring, retry policies, and notifications
# ============================================================================

# -----------------------------------
# Action Group for ADF Failure Notifications
# -----------------------------------
resource "azurerm_monitor_action_group" "adf_failure_alerts" {
  name                = "ag-adf-failures-${var.environment}"
  resource_group_name = azurerm_resource_group.main.name
  short_name          = "ADF-FAIL"

  email_receiver {
    name           = "DataTeamEmail"
    email_address  = var.alert_email_address
    use_common_alert_schema = true
  }

  # Uncomment to add Slack webhook (requires var.slack_webhook_url)
  # webhook_receiver {
  #   name        = "SlackNotification"
  #   service_uri = var.slack_webhook_url
  #   use_common_alert_schema = true
  # }

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "monitoring"
  }
}

# -----------------------------------
# Metric Alert: Pipeline Failures
# Triggers when orchestration_pipeline fails
# -----------------------------------
resource "azurerm_monitor_metric_alert" "adf_pipeline_failure" {
  name                = "adf-orchestration-pipeline-failure-alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_data_factory.main.id]
  description         = "Alert when orchestration_pipeline has failed runs"
  frequency           = "PT1M"  # Evaluate every 1 minute
  window_size         = "PT5M"  # Check last 5 minutes
  enabled             = true

  criteria {
    metric_name       = "PipelineFailedRuns"
    metric_namespace  = "Microsoft.DataFactory/factories"
    aggregation       = "Total"
    operator          = "GreaterThan"
    threshold         = 0

    dimension {
      name     = "PipelineName"
      operator = "Include"
      values   = ["orchestration_pipeline"]
    }
  }

  action {
    action_group_id = azurerm_monitor_action_group.adf_failure_alerts.id
  }

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# -----------------------------------
# Metric Alert: Activity Failures
# Triggers on any failed activity in the pipeline
# -----------------------------------
resource "azurerm_monitor_metric_alert" "adf_activity_failure" {
  name                = "adf-activity-failure-alert"
  resource_group_name = azurerm_resource_group.main.name
  scopes              = [azurerm_data_factory.main.id]
  description         = "Alert when any pipeline activity fails"
  frequency           = "PT1M"
  window_size         = "PT5M"
  enabled             = true

  criteria {
    metric_name      = "ActivityFailedRuns"
    metric_namespace = "Microsoft.DataFactory/factories"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.adf_failure_alerts.id
  }

  tags = {
    environment = var.environment
    project     = var.project_name
  }
}

# -----------------------------------
# Diagnostic Settings: Send ADF logs to Log Analytics
# For detailed debugging and long-term retention
# -----------------------------------
resource "azurerm_monitor_diagnostic_setting" "adf_diagnostics" {
  name                       = "adf-diagnostics"
  target_resource_id         = azurerm_data_factory.main.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.monitoring.id

  enabled_log {
    category = "PipelineRuns"
  }

  enabled_log {
    category = "ActivityRuns"
  }

  enabled_log {
    category = "TriggerRuns"
  }

  metric {
    category = "AllMetrics"
    enabled  = true
  }
}

# -----------------------------------
# Log Analytics Workspace (for centralized monitoring)
# -----------------------------------
resource "azurerm_log_analytics_workspace" "monitoring" {
  name                = "law-adf-${var.environment}"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  sku                 = "PerGB2018"
  retention_in_days   = 30

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "monitoring"
  }
}

# -----------------------------------
# KQL Queries for Log Analytics Monitoring
# (These are examples of queries to run in Log Analytics)
# -----------------------------------
resource "azurerm_monitor_scheduled_query_rules_alert" "pipeline_failure_rate" {
  name                = "high-pipeline-failure-rate"
  location            = azurerm_resource_group.main.location
  resource_group_name = azurerm_resource_group.main.name
  data_source_id      = azurerm_log_analytics_workspace.monitoring.id

  # KQL Query: Calculate failure rate in last 1 hour
  query = <<-QUERY
    ADFPipelineRun
    | where PipelineName == "orchestration_pipeline"
    | where TimeGenerated > ago(1h)
    | summarize 
        TotalRuns = count(),
        FailedRuns = countif(Status == "Failed"),
        FailureRate = (countif(Status == "Failed") * 100.0) / count()
    | where FailureRate > 50
  QUERY

  trigger {
    operator  = "GreaterThan"
    threshold = 0
  }

  action {
    action_group_id = azurerm_monitor_action_group.adf_failure_alerts.id
  }

  enabled = true
  severity = 3

  description = "Alert if pipeline failure rate exceeds 50% in last hour"

  depends_on = [azurerm_log_analytics_workspace.monitoring]
}

# -----------------------------------
# Application Insights Integration
# For detailed Function execution metrics
# -----------------------------------
resource "azurerm_application_insights_smart_detection_rule" "function_failures" {
  name                       = "function-failure-detection"
  application_insights_id    = azurerm_application_insights.functions.id
  rule_definition_id         = "Spikeanomalyrule"  # Built-in spike detection
  enabled                    = true
  send_emails_to_subscription_owners = true
  additional_email_addresses = [var.alert_email_address]
}

# -----------------------------------
# Storage Account: Dead Letter Queue
# For failed messages requiring manual replay
# -----------------------------------
resource "azurerm_storage_data_lake_gen2_path" "dead_letter" {
  path               = "dead-letter"
  filesystem_name    = azurerm_storage_data_lake_gen2_filesystem.main.name
  storage_account_id = azurerm_storage_account.datalake.id
  resource           = "directory"

  depends_on = [azurerm_storage_data_lake_gen2_filesystem.main]
}

# -----------------------------------
# Azure SQL Database: Pipeline Run History
# Track all pipeline runs for circuit breaker pattern
# -----------------------------------
resource "azurerm_mssql_database" "monitoring" {
  name           = "adf-monitoring"
  server_id      = azurerm_mssql_server.monitoring.id
  collation      = "SQL_Latin1_General_CP1_CI_AS"
  license_type   = "LicenseIncluded"
  max_size_gb    = 2
  sku_name       = "S0"  # Standard tier (cheap)

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "monitoring"
  }
}

resource "azurerm_mssql_server" "monitoring" {
  name                         = "sql-adf-monitoring-${random_string.suffix.result}"
  resource_group_name          = azurerm_resource_group.main.name
  location                     = azurerm_resource_group.main.location
  version                      = "12.0"
  administrator_login          = "sqladmin"
  administrator_login_password = var.sql_admin_password

  tags = {
    environment = var.environment
    project     = var.project_name
    component   = "monitoring"
  }
}

# -----------------------------------
# Outputs: Alert Configuration
# -----------------------------------
output "action_group_id" {
  value       = azurerm_monitor_action_group.adf_failure_alerts.id
  description = "Action Group ID for ADF failure notifications"
}

output "log_analytics_workspace_id" {
  value       = azurerm_log_analytics_workspace.monitoring.id
  description = "Log Analytics Workspace ID for centralized logging"
}

output "dead_letter_path" {
  value       = "dead-letter/"
  description = "ADLS path for dead letter messages"
}

output "monitoring_database_connection_string" {
  value       = "Server=tcp:${azurerm_mssql_server.monitoring.fully_qualified_domain_name},1433;Initial Catalog=adf-monitoring;Persist Security Info=False;User ID=sqladmin;Password=***;MultipleActiveResultSets=False;Encrypt=True;TrustServerCertificate=False;Connection Timeout=30;"
  description = "Connection string for monitoring database"
  sensitive   = true
}
