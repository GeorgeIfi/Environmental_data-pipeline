# Azure-Native ETL Orchestration Guide

This guide covers deploying and executing the fully Azure-native ETL pipeline using Azure Data Factory and Azure Functions.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Data Factory                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────┐      ┌──────────────────┐            │
│  │   Web Activity   │─────▶│   Web Activity   │─────┐      │
│  │ Bronze Ingest    │      │ Silver Transform │     │      │
│  └──────────────────┘      └──────────────────┘     │      │
│                                                      ▼      │
│                                            ┌──────────────────┐│
│                                            │   Web Activity   ││
│                                            │ Gold Transform   ││
│                                            └──────────────────┘│
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │              │                         │
         ▼              ▼                         ▼
    ┌─────────┐  ┌─────────┐  ┌──────────────────────┐
    │ Function│  │ Function│  │ Azure Functions      │
    │ Storage │  │ Storage │  │ (Consumption Tier)   │
    │ Account │  │ Account │  │                      │
    └─────────┘  └─────────┘  │ • bronze-ingest     │
                               │ • silver-transform  │
                               │ • gold-transform    │
                               └──────────────────────┘
                                      ↓
                               ┌──────────────────┐
                               │ ADLS Gen2 Storage│
                               │                  │
                               │ • landing/       │
                               │ • bronze/        │
                               │ • silver/        │
                               │ • gold/          │
                               └──────────────────┘
```

## Prerequisites

1. **Azure CLI** installed and authenticated
2. **Terraform** v1.7.0+
3. **Azure Functions Core Tools** (installed by deploy script)
4. **Python 3.10+** with dependencies installed
5. **.env file** with Azure credentials

## Phase 1: Deploy Infrastructure

### 1.1 Provision Azure Resources with Terraform

```bash
# Navigate to Terraform directory
cd infra/terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply configuration (creates ~30 resources including Function App)
terraform apply
```

**Resources Created:**
- Resource Group: `rg-envpipeline-dev`
- ADLS Gen2 Storage Account: `stenvpipelineXXXX`
- Function App: `func-envpipelineXXXX`
- Function App Storage: `stfuncenvpipelineXXXX`
- Data Factory: `adf-environmentalXXXX`
- Synapse Workspace: `syn-envpipeline-dev-XXXX`
- Container Registry: `acrenvironmentalXXXX`
- Application Insights for monitoring
- RBAC role assignments for Managed Identity

### 1.2 Verify Terraform Outputs

```bash
# Get terraform outputs
terraform output -json

# Key outputs to note:
# - function_app_name: Name of deployed Function App
# - function_app_endpoint: HTTPS URL for function calls
# - storage_account_name: ADLS Gen2 storage account
```

## Phase 2: Deploy Azure Functions

### 2.1 Automated Deployment

```bash
# From project root
chmod +x deploy_functions.sh
./deploy_functions.sh
```

This script will:
1. Extract Function App name from terraform outputs
2. Install Azure Functions Core Tools (if needed)
3. Install Python dependencies
4. Build and deploy functions to Azure
5. Display function endpoint URLs

### 2.2 Manual Deployment (Alternative)

```bash
# Install functions core tools
npm install -g azure-functions-core-tools@4

# Navigate to functions directory
cd azure_functions

# Install dependencies
pip install -r requirements.txt

# Get function app name from terraform
FUNC_APP_NAME=$(terraform -chdir=../infra/terraform output -raw function_app_name)

# Deploy to Azure
func azure functionapp publish $FUNC_APP_NAME --build remote

# Verify deployment
func azure functionapp list-functions $FUNC_APP_NAME
```

## Phase 3: Test Individual Functions

### 3.1 Get Function URLs

```bash
# Extract function endpoint
FUNC_ENDPOINT=$(terraform -chdir=infra/terraform output -raw function_app_endpoint)

# Get storage account details
STORAGE_ACCOUNT=$(terraform -chdir=infra/terraform output -raw storage_account_name)
STORAGE_KEY=$(terraform -chdir=infra/terraform output -raw storage_account_key)
```

### 3.2 Test Bronze Ingestion Function

```bash
curl -X POST \
  "${FUNC_ENDPOINT}/api/bronze-ingest" \
  -H "Content-Type: application/json" \
  -d "{
    \"storage_account\": \"${STORAGE_ACCOUNT}\",
    \"storage_key\": \"${STORAGE_KEY}\",
    \"container\": \"environmental-data\",
    \"csv_file\": \"landing/weather_raw.csv\"
  }"
```

**Expected Response:**
```json
{
  "status": "success",
  "stage": "bronze_ingestion",
  "rows_ingested": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/bronze/raw_data.parquet"
}
```

### 3.3 Test Silver Transformation Function

```bash
curl -X POST \
  "${FUNC_ENDPOINT}/api/silver-transform" \
  -H "Content-Type: application/json" \
  -d "{
    \"storage_account\": \"${STORAGE_ACCOUNT}\",
    \"storage_key\": \"${STORAGE_KEY}\",
    \"container\": \"environmental-data\",
    \"bronze_file\": \"bronze/raw_data.parquet\"
  }"
```

**Expected Response:**
```json
{
  "status": "success",
  "stage": "silver_transformation",
  "rows_cleaned": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/silver/cleaned_data.parquet"
}
```

### 3.4 Test Gold Transformation Function

```bash
curl -X POST \
  "${FUNC_ENDPOINT}/api/gold-transform" \
  -H "Content-Type: application/json" \
  -d "{
    \"storage_account\": \"${STORAGE_ACCOUNT}\",
    \"storage_key\": \"${STORAGE_KEY}\",
    \"container\": \"environmental-data\",
    \"silver_file\": \"silver/cleaned_data.parquet\"
  }"
```

**Expected Response:**
```json
{
  "status": "success",
  "stage": "gold_aggregation",
  "rows_aggregated": 2174,
  "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/gold/analytics_data.parquet"
}
```

## Phase 4: Execute ADF Pipeline

### 4.1 Trigger Pipeline Manually in Azure Portal

1. Navigate to Azure Data Factory
2. Go to **Pipelines** section
3. Select **OrchestrationPipeline**
4. Click **Trigger** → **Trigger Now**
5. Review and confirm

### 4.2 Monitor Pipeline Execution

1. Go to **Monitor** → **Pipeline Runs**
2. Select your pipeline run
3. Click on each activity to view:
   - Execution status
   - Duration
   - Input/Output details
   - Error messages (if any)

### 4.3 Check Output Data

After successful execution, verify data in storage:

```bash
# List files in each layer
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name environmental-data \
  --prefix bronze/

az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name environmental-data \
  --prefix silver/

az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --account-key $STORAGE_KEY \
  --container-name environmental-data \
  --prefix gold/
```

## Phase 5: Configure Automated Triggers

### 5.1 Blob Event Trigger (Recommended)

Automatically triggers pipeline when CSV is uploaded to `landing/` folder:

**Already configured in Terraform** via `azurerm_data_factory_trigger_blob_event`

To modify trigger:
1. Go to **Data Factory** → **Triggers**
2. Select **LandingFolderTrigger**
3. Edit conditions if needed
4. Ensure **Activated** is checked

### 5.2 Scheduled Trigger (Alternative)

To create a daily schedule:

1. In Data Factory Studio, go to **Triggers** → **New Trigger**
2. Name: `DailyETLTrigger`
3. Type: **Schedule**
4. Recurrence: Daily at desired time
5. Link to **OrchestrationPipeline**

Example JSON:
```json
{
  "name": "DailyETLTrigger",
  "type": "ScheduleTrigger",
  "description": "Daily ETL execution at 2 AM UTC",
  "runtimeState": "Started",
  "typeProperties": {
    "recurrence": {
      "frequency": "Day",
      "interval": 1,
      "startTime": "2024-01-01T02:00:00Z",
      "timeZone": "UTC"
    }
  }
}
```

## Phase 6: Monitoring and Troubleshooting

### 6.1 Application Insights Dashboard

View function performance and errors:

```bash
# Get Application Insights resource name
APP_INSIGHTS=$(terraform -chdir=infra/terraform output -raw function_app_name | sed 's/func-/appins-/')

# View recent traces
az monitor app-insights metrics show \
  --resource-group rg-envpipeline-dev \
  --app $APP_INSIGHTS \
  --metric requests/count
```

### 6.2 Function Logs

Real-time function execution logs:

```bash
# Stream function logs
az functionapp log tail \
  --name $(terraform -chdir=infra/terraform output -raw function_app_name) \
  --resource-group rg-envpipeline-dev
```

### 6.3 Common Issues and Solutions

| Issue | Solution |
|-------|----------|
| **Function returns 401 Unauthorized** | Function App auth level must be "Anonymous" for ADF calls. Check function.json `authLevel`. |
| **Storage access denied** | Verify RBAC role assignment: `Storage Blob Data Contributor` should be assigned to Function App Managed Identity. |
| **Function timeout (5 min exceeded)** | Reduce CSV file size or optimize transformation logic. Consider async processing for large datasets. |
| **"No such file or directory" for parquet** | Verify blob paths are correct and files exist in storage containers. |
| **ADF pipeline fails silently** | Check Application Insights traces and function logs for detailed error information. |

### 6.4 View Full Execution Metrics

```bash
# Pipeline run details
az datafactory pipeline-run query-by-factory \
  --factory-name $(terraform -chdir=infra/terraform output -raw data_factory_name) \
  --resource-group rg-envpipeline-dev \
  --filters operand=PipelineName operator=Equals values=OrchestrationPipeline
```

## Phase 7: Performance Optimization

### 7.1 Function App Scaling

Current configuration uses **Consumption (Y1)** tier:
- **Cost**: Pay per execution + storage
- **Auto-scaling**: Automatic
- **Suitable for**: Variable, unpredictable workloads

To switch to **Premium** tier for better performance:

```bash
# Edit variables.tf and set:
# function_app_sku = "Premium"
# Then run terraform apply
```

### 7.2 Parallel Execution

To run multiple CSV files simultaneously:

Update ADF pipeline to use **ForEach** activity:
```json
{
  "name": "ProcessMultipleFilesLoop",
  "type": "ForEach",
  "typeProperties": {
    "items": {
      "value": "@split(pipeline().parameters.csvFiles, ',')",
      "type": "Expression"
    },
    "activities": [
      {
        "name": "BronzeIngestActivity",
        "type": "WebActivity",
        ...
      }
    ]
  }
}
```

### 7.3 Caching Strategy

Implement caching for frequently accessed data:
- Bronze layer: No caching (source of truth)
- Silver layer: Cache cleaned data for 24 hours
- Gold layer: Cache aggregations for 1 hour

## Phase 8: Data Validation

### 8.1 Row Count Validation

Compare row counts across layers:

```bash
# After pipeline execution, verify:
# Bronze: Should match input CSV
# Silver: Should equal or be less than Bronze (after filtering)
# Gold: Should equal unique date/location combinations
```

### 8.2 Schema Validation

Ensure consistent column names and data types across layers:

```bash
# Use Synapse SQL to query schema
az synapse workspace firewall-rule create \
  --name AllowMyIP \
  --resource-group rg-envpipeline-dev \
  --workspace-name syn-envpipeline-dev-XXXX \
  --start-ip-address $(curl -s https://api.ipify.org) \
  --end-ip-address $(curl -s https://api.ipify.org)
```

## Phase 9: Cleanup (When Done)

### 9.1 Delete All Azure Resources

```bash
# Destroy Terraform resources
cd infra/terraform
terraform destroy

# Verify deletion
az group delete \
  --name rg-envpipeline-dev \
  --no-wait
```

### 9.2 Clean Up Local Files

```bash
# Remove terraform state (if rebuilding)
rm terraform.tfstate*
rm .terraform.lock.hcl
```

## Success Criteria

✅ **Infrastructure Deployed**
- [ ] Function App running in Azure
- [ ] Storage account contains environmental-data container
- [ ] Data Factory created with OrchestrationPipeline

✅ **Functions Operational**
- [ ] bronze-ingest returns HTTP 200 with row count
- [ ] silver-transform returns HTTP 200 with cleaned row count
- [ ] gold-transform returns HTTP 200 with aggregation count

✅ **Pipeline Execution**
- [ ] All 3 Web Activities complete successfully
- [ ] Bronze/silver/gold parquet files appear in storage
- [ ] Row counts are consistent across layers

✅ **Monitoring Active**
- [ ] Application Insights shows function invocations
- [ ] Execution logs visible in Azure Portal
- [ ] Performance metrics available for optimization

## Next Steps

1. **Schedule Automatic Triggers**: Configure daily ETL execution
2. **Add Data Quality Checks**: Implement validation in silver/gold layers
3. **Create BI Dashboards**: Connect Power BI to gold layer data
4. **Implement Cost Monitoring**: Set up Azure Cost Management alerts
5. **Document SLAs**: Define acceptable performance and availability metrics
