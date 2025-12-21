#!/bin/bash

# Deploy Azure infrastructure
cd infra/terraform

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="sql_admin_password=YourSecurePassword123!"

# Apply (uncomment to deploy)
# terraform apply -var="sql_admin_password=YourSecurePassword123!" -auto-approve

echo "Infrastructure deployment complete"