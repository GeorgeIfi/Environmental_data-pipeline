# Azure Pipeline Deployment Guide

## Prerequisites

- Azure CLI installed and authenticated
- Terraform installed
- Python 3.11+ with pip
- Azure subscription with appropriate permissions

## Step 1: Infrastructure Deployment

### 1.1 Initialize Terraform
```bash
cd infra/terraform
terraform init
```

### 1.2 Configure Variables
Create `terraform.tfvars`:
```hcl
project_name = "envpipeline"
environment = "dev"
location = "UK South"
sql_admin_username = "synadmin"
sql_admin_password = "YourSecurePassword123!"
```

### 1.3 Deploy Infrastructure
```bash
terraform plan
terraform apply -auto-approve
```

### 1.4 Capture Outputs
```bash
terraform output -json > ../outputs.json
```

## Step 2: Environment Configuration

### 2.1 Update .env File
Update `.env` with Terraform outputs:
```bash
# Extract values from terraform output
AZURE_STORAGE_ACCOUNT_NAME=$(terraform output -raw storage_account_name)
AZURE_STORAGE_ACCOUNT_KEY=$(terraform output -raw storage_account_key)
AZURE_DATA_FACTORY_NAME=$(terraform output -raw data_factory_name)
AZURE_RESOURCE_GROUP=$(terraform output -raw resource_group_name)
```

### 2.2 Set Service Principal Credentials
```bash
AZURE_CLIENT_ID=$(terraform output -raw service_principal_app_id)
AZURE_CLIENT_SECRET=$(terraform output -raw service_principal_password)
```

## Step 3: Code Packaging

### 3.1 Install Dependencies
```bash
pip install -r requirements.txt
```

### 3.2 Create Deployment Package
```bash
python package_pipeline.py
```

### 3.3 Upload Code Package
```bash
# Upload env_pipeline.zip to Azure Storage
az storage blob upload \
  --account-name $AZURE_STORAGE_ACCOUNT_NAME \
  --container-name environmental-data \
  --name code/env_pipeline.zip \
  --file artifacts/env_pipeline.zip
```

## Step 4: ADF Pipeline Deployment

### 4.1 Deploy Pipeline
```bash
cd src/orchestration
python deploy_adf_orchestration.py
```

### 4.2 Verify Deployment
- Go to Azure Portal → Data Factory
- Check pipeline "EnvironmentalDataPipeline" exists
- Verify trigger "DailyEnvironmentalDataTrigger" is active

## Step 5: Testing

### 5.1 Local Test
```bash
python run_pipeline.py --raw-path data/raw/weather_raw.csv
```

### 5.2 Manual ADF Trigger
```bash
az datafactory pipeline create-run \
  --factory-name $AZURE_DATA_FACTORY_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --pipeline-name EnvironmentalDataPipeline
```

### 5.3 Monitor Execution
- Azure Portal → Data Factory → Monitor
- Check pipeline run status and logs

## Step 6: Validation

### 6.1 Check Data Lake
```bash
az storage blob list \
  --account-name $AZURE_STORAGE_ACCOUNT_NAME \
  --container-name environmental-data \
  --prefix bronze/weather/
```

### 6.2 Verify Synapse Access
- Azure Portal → Synapse Studio
- Query external tables in SQL pool

## Troubleshooting

### Common Issues
1. **Authentication Errors**: Verify service principal permissions
2. **Batch Pool Issues**: Check pool status and node availability
3. **Storage Access**: Ensure RBAC roles are assigned correctly

### Debug Commands
```bash
# Check ADF pipeline status
az datafactory pipeline-run show \
  --factory-name $AZURE_DATA_FACTORY_NAME \
  --resource-group $AZURE_RESOURCE_GROUP \
  --run-id <run-id>

# View Batch job logs
az batch job list --account-name <batch-account>
```

## Cleanup

### Remove All Resources
```bash
cd infra/terraform
terraform destroy -auto-approve
```

## Reusability Checklist

- [ ] Infrastructure deployed via Terraform
- [ ] Environment variables configured
- [ ] Code package uploaded to storage
- [ ] ADF pipeline deployed and active
- [ ] Local and cloud testing completed
- [ ] Monitoring and logging verified
- [ ] Documentation updated with any customizations