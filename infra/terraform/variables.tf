variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
  sensitive   = true
  nullable    = false
}

variable "tenant_id" {
  description = "Azure tenant ID"
  type        = string
  sensitive   = true
  nullable    = false
}

variable "location" {
  description = "Azure region for deployment"
  type        = string
  default     = "uksouth"
}

variable "environment" {
  description = "Deployment environment (e.g. dev/test/prod)"
  type        = string
  default     = "dev"
}

variable "sql_admin_username" {
  description = "Synapse SQL admin username"
  type        = string
  default     = "synadmin" # optional, ok for dev
}

variable "sql_admin_password" {
  description = "Synapse SQL admin password"
  type        = string
  sensitive   = true
  nullable    = false
}

variable "project_name" {
  description = "Short name of the project for resource naming"
  type        = string
  default     = "envpipeline"
}

variable "client_ip" {
  description = "Public IPv4 of developer machine for Synapse firewall"
  type        = string
  nullable    = false
}

# ============================================================================
# Monitoring & Alert Variables (New)
# ============================================================================

variable "alert_email_address" {
  description = "Email address for ADF failure alerts"
  type        = string
  default     = "data-team@company.com"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications (optional)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed Azure Monitor metrics and logging"
  type        = bool
  default     = true
}

variable "service_principal_id" {
  description = "Azure AD Service Principal App ID for authentication"
  type        = string
  sensitive   = true
  nullable    = false
}
