# Quick Deployment Reference

## Prerequisites Checklist
- [ ] Azure CLI installed: `az --version`
- [ ] Logged in to Azure: `az login`
- [ ] Terraform 1.7.0+: `terraform --version`
- [ ] Python 3.10+: `python3 --version`
- [ ] `.env` file exists with Azure credentials
- [ ] `data/raw/weather_raw.csv` exists locally

## One-Line Deployment

```bash
# 1. Deploy infrastructure
cd infra/terraform && terraform apply -auto-approve && cd ../..

# 2. Deploy functions
chmod +x deploy_functions.sh && ./deploy_functions.sh

# 3. Upload test data (after terraform output shows storage account name)
STORAGE=$(terraform -chdir=infra/terraform output -raw storage_account_name 2>/dev/null || echo "stenvpipelineXXXX")
STORAGE_KEY=$(terraform -chdir=infra/terraform output -raw storage_account_key 2>/dev/null)
az storage blob upload --account-name $STORAGE --account-key "$STORAGE_KEY" \
  --container-name environmental-data --name landing/weather_raw.csv \
  --file data/raw/weather_raw.csv

# 4. Trigger pipeline in Azure Portal or use curl
ENDPOINT=$(terraform -chdir=infra/terraform output -raw function_app_endpoint 2>/dev/null || echo "https://func-envpipeline-XXXX.azurewebsites.net")
curl -X POST "$ENDPOINT/api/bronze-ingest" -H "Content-Type: application/json" \
  -d "{\"storage_account\":\"$STORAGE\",\"storage_key\":\"$STORAGE_KEY\",\"container\":\"environmental-data\",\"csv_file\":\"landing/weather_raw.csv\"}"
```

## Key Commands

### Infrastructure
```bash
cd infra/terraform

# Initialize Terraform (first time only)
terraform init

# Validate configuration
terraform validate

# Preview changes
terraform plan

# Apply configuration
terraform apply

# Get outputs
terraform output -json

# Destroy all resources (caution!)
terraform destroy
```

### Functions
```bash
# Deploy functions
./deploy_functions.sh

# View logs
az functionapp log tail --name func-envpipeline-XXXX --resource-group rg-envpipeline-dev

# List functions
az functionapp function list --name func-envpipeline-XXXX --resource-group rg-envpipeline-dev
```

### Storage
```bash
# Upload CSV to landing folder
az storage blob upload \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name environmental-data \
  --name landing/weather_raw.csv \
  --file data/raw/weather_raw.csv

# List bronze layer files
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name environmental-data \
  --prefix bronze/
```

### ADF Pipeline
```bash
# Trigger pipeline manually (in Portal)
# Data Factory → Pipelines → OrchestrationPipeline → Trigger Now

# Or via Azure CLI
az datafactory pipeline-run create \
  --factory-name adf-environmental-XXXX \
  --resource-group rg-envpipeline-dev \
  --name OrchestrationPipeline
```

## Environment Variables (Extract from Terraform)

```bash
# Save to shell session
export STORAGE_ACCOUNT=$(terraform -chdir=infra/terraform output -raw storage_account_name)
export STORAGE_KEY=$(terraform -chdir=infra/terraform output -raw storage_account_key)
export FUNC_ENDPOINT=$(terraform -chdir=infra/terraform output -raw function_app_endpoint)
export RESOURCE_GROUP=$(terraform -chdir=infra/terraform output -raw resource_group_name)
export DATA_FACTORY=$(terraform -chdir=infra/terraform output -raw data_factory_name)
export FUNC_APP=$(terraform -chdir=infra/terraform output -raw function_app_name)

# Verify
echo "Storage: $STORAGE_ACCOUNT"
echo "Functions: $FUNC_ENDPOINT"
echo "Data Factory: $DATA_FACTORY"
```

## Testing Functions Locally (Before Deployment)

```bash
cd azure_functions

# Install dependencies
pip install -r requirements.txt

# Start local runtime
func start

# In another terminal, test function
curl -X POST http://localhost:7071/api/bronze-ingest \
  -H "Content-Type: application/json" \
  -d '{
    "storage_account": "stenvpipelineXXXX",
    "storage_key": "your-storage-key",
    "container": "environmental-data",
    "csv_file": "landing/weather_raw.csv"
  }'
```

## Expected Responses

### Bronze Ingest
```json
{
  "status": "success",
  "stage": "bronze_ingestion",
  "rows_ingested": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/bronze/raw_data.parquet"
}
```

### Silver Transform
```json
{
  "status": "success",
  "stage": "silver_transformation",
  "rows_cleaned": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/silver/cleaned_data.parquet"
}
```

### Gold Transform
```json
{
  "status": "success",
  "stage": "gold_aggregation",
  "rows_aggregated": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/gold/analytics_data.parquet"
}
```

## Monitoring URLs (After Deployment)

- **Azure Portal**: https://portal.azure.com
  - Resource Group: `rg-envpipeline-dev`
  - Function App: `func-envpipeline-XXXX`
  - Data Factory: `adf-environmental-XXXX`

- **Application Insights**: Filter by function name
  - Resource: `appins-envpipeline-functions`

- **Storage Explorer**: View data in layers
  - Account: `stenvpipelineXXXX`
  - Paths: `bronze/`, `silver/`, `gold/`

## Troubleshooting Quick Fixes

| Symptom | Fix |
|---------|-----|
| Terraform plan shows errors | Run `terraform validate`, check .env file |
| Functions won't deploy | Ensure Azure CLI logged in: `az login` |
| 401 Unauthorized on function call | Check function auth level in function.json |
| Storage access denied | Verify RBAC role assignment in portal |
| ADF pipeline fails | Check Application Insights for function errors |
| Cold start slow (first call) | Expected on Consumption tier (~15-30 sec) |
| CSV file not found | Upload to `landing/weather_raw.csv` path |

## Cost Monitoring

```bash
# View resource costs (requires Azure Cost Management)
az costmanagement query create \
  --scope "/subscriptions/e95dfdc7-63c1-4225-9ec2-900f1cb5224a/resourceGroups/rg-envpipeline-dev"
```

**Expected monthly cost**: ~$22-25 (based on daily runs)
- Function executions: ~$0.20/day
- Storage operations: ~$0.02/day
- Data Factory: ~$0.50/day

## Cleanup Commands

```bash
# Delete all resources
cd infra/terraform
terraform destroy -auto-approve

# Verify deletion
az group delete --name rg-envpipeline-dev

# Clean local files
rm terraform.tfstate*
rm .terraform.lock.hcl
```

## Files to Reference

- **Detailed guide**: [ADF_ORCHESTRATION.md](ADF_ORCHESTRATION.md) (630 lines)
- **Function specs**: [azure_functions/README.md](azure_functions/README.md)
- **Implementation summary**: [AZURE_FUNCTIONS_IMPLEMENTATION.md](AZURE_FUNCTIONS_IMPLEMENTATION.md)
- **Main README**: [README.md](README.md)
- **Terraform code**: [infra/terraform/](infra/terraform/)
