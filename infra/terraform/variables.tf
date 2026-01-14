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
