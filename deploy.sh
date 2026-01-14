#!/bin/bash
# Azure Pipeline Deployment Script
set -e

echo "=== Azure Environmental Data Pipeline Deployment ==="

# Step 1: Navigate to Terraform directory
echo "Step 1: Initializing Terraform..."
cd infra/terraform

# Step 2: Initialize Terraform
terraform init

# Step 3: Create terraform.tfvars if it doesn't exist
if [ ! -f terraform.tfvars ]; then
    echo "Step 2: Creating terraform.tfvars..."
    cat > terraform.tfvars << EOF
project_name = "envpipeline"
environment = "dev"
location = "UK South"
sql_admin_username = "synadmin"
sql_admin_password = "SecurePassword123!"
EOF
    echo "✓ Created terraform.tfvars"
else
    echo "✓ terraform.tfvars already exists"
fi

# Step 4: Plan infrastructure
echo "Step 3: Planning infrastructure..."
terraform plan

# Step 5: Apply infrastructure (with confirmation)
echo "Step 4: Deploying infrastructure..."
read -p "Deploy infrastructure? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    terraform apply -auto-approve
    
    # Step 6: Extract outputs
    echo "Step 5: Extracting outputs..."
    terraform output -json > ../outputs.json
    
    echo "✓ Infrastructure deployed successfully!"
    echo "Next steps:"
    echo "1. Update .env file with terraform outputs"
    echo "2. Run: python package_pipeline.py"
    echo "3. Upload code package to Azure Storage"
    echo "4. Deploy ADF pipeline"
else
    echo "Deployment cancelled"
    exit 1
fi