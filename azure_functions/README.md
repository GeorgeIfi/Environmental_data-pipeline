# Azure Functions ETL

This directory contains the Azure Functions implementations for the medallion architecture ETL pipeline. Each function is an HTTP-triggered endpoint that wraps the corresponding Pandas transformation logic.

## Functions

### 1. Bronze Ingestion (`bronze_ingestion/`)
- **Route**: `/api/bronze-ingest`
- **Method**: POST
- **Purpose**: Ingests CSV data from Azure Storage to Bronze layer (parquet format)
- **Request Body**:
  ```json
  {
    "storage_account": "stenvpipelineXXXX",
    "storage_key": "storage_account_key",
    "container": "environmental-data",
    "csv_file": "landing/weather_raw.csv"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "stage": "bronze_ingestion",
    "rows_ingested": 2174,
    "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/bronze/raw_data.parquet"
  }
  ```

### 2. Silver Transformation (`silver_transformation/`)
- **Route**: `/api/silver-transform`
- **Method**: POST
- **Purpose**: Cleans and validates data from Bronze to Silver layer
- **Request Body**:
  ```json
  {
    "storage_account": "stenvpipelineXXXX",
    "storage_key": "storage_account_key",
    "container": "environmental-data",
    "bronze_file": "bronze/raw_data.parquet"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "stage": "silver_transformation",
    "rows_cleaned": 2174,
    "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/silver/cleaned_data.parquet"
  }
  ```

### 3. Gold Transformation (`gold_transformation/`)
- **Route**: `/api/gold-transform`
- **Method**: POST
- **Purpose**: Aggregates data from Silver to Gold layer for analytics
- **Request Body**:
  ```json
  {
    "storage_account": "stenvpipelineXXXX",
    "storage_key": "storage_account_key",
    "container": "environmental-data",
    "silver_file": "silver/cleaned_data.parquet"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "stage": "gold_aggregation",
    "rows_aggregated": 2174,
    "output_path": "https://stenvpipelineXXXX.blob.core.windows.net/environmental-data/gold/analytics_data.parquet"
  }
  ```

## Local Development

### Prerequisites
- Python 3.10+
- Azure Functions Core Tools: `npm install -g azure-functions-core-tools@4`
- Azure CLI: `az login`

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure local settings
# Edit local.settings.json with your Azure Storage connection string
```

### Run Locally
```bash
# Start the function runtime
func start

# In another terminal, test a function
curl -X POST http://localhost:7071/api/bronze-ingest \
  -H "Content-Type: application/json" \
  -d '{
    "storage_account": "mystorageacct",
    "storage_key": "mykey",
    "container": "environmental-data",
    "csv_file": "landing/weather_raw.csv"
  }'
```

## Deployment to Azure

### Option 1: Automated Deployment
```bash
cd /path/to/project
./deploy_functions.sh
```

### Option 2: Manual Deployment
```bash
# From project root, run Terraform to provision infrastructure
cd infra/terraform
terraform apply

# Deploy functions using Azure Functions Core Tools
cd ../../azure_functions
func azure functionapp publish <function-app-name> --build remote
```

### Option 3: Using Azure Portal
1. Go to Azure Portal → Function Apps
2. Select the deployed Function App
3. Use Deployment Center → GitHub / Local Git to configure CI/CD
4. Push code to trigger automatic deployments

## Architecture

The functions are orchestrated by Azure Data Factory using a 3-stage pipeline:

```
[CSV File Uploaded] 
        ↓
[ADF Trigger: Blob Event]
        ↓
[Web Activity 1: bronze-ingest] → Bronze layer (parquet)
        ↓
[Web Activity 2: silver-transform] → Silver layer (cleaned parquet)
        ↓
[Web Activity 3: gold-transform] → Gold layer (aggregated parquet)
```

## Monitoring

### Azure Portal
1. Navigate to the Function App
2. View execution logs and metrics in the Overview blade
3. Check Application Insights for detailed telemetry

### Local Testing with Application Insights
Functions automatically send telemetry to Application Insights when deployed. View insights:
```bash
az monitor app-insights metrics show --resource-group rg-envpipeline-dev --app appins-envpipeline-functions
```

## Error Handling

All functions include try-catch blocks that return HTTP 500 with error details:
```json
{
  "status": "error",
  "stage": "bronze_ingestion",
  "error": "Error message details"
}
```

Check Azure Monitor or Application Insights for full error traces.

## Performance Considerations

- **Consumption Tier**: Functions use Azure's Consumption tier for cost-efficiency (pay only for execution)
- **Cold Starts**: First invocation may take 10-30 seconds; subsequent calls are faster
- **Timeout**: Default 5 minutes per function execution
- **Memory**: Consumption tier scales automatically based on demand

## Environment Variables

Functions access Azure Storage via:
- `DATA_LAKE_STORAGE_ACCOUNT_NAME`: ADLS Gen2 account name
- `DATA_LAKE_STORAGE_ACCOUNT_KEY`: Storage account access key
- `DATA_LAKE_CONTAINER_NAME`: Default container name

These are configured in Terraform and available in the Function App application settings.

## Troubleshooting

### Functions not triggering from ADF
- Check ADF pipeline execution history for Web Activity errors
- Verify function app URLs are accessible
- Ensure Function App has "Anonymous" authentication (required for ADF)

### Data not appearing in storage
- Check function logs: `az functionapp log tail --name <function-app-name> --resource-group <rg-name>`
- Verify storage account key is correct and not expired
- Confirm container "environmental-data" exists

### Python dependencies missing
- Ensure requirements.txt is included in deployment
- Verify dependencies are installed: `pip install -r requirements.txt`
- Check function app logs for import errors

## Next Steps

1. **Test Pipeline**: Trigger ADF pipeline manually to validate end-to-end execution
2. **Configure Triggers**: Set up blob event trigger or scheduled trigger in ADF
3. **Monitor Performance**: Review Application Insights dashboards
4. **Scale Configuration**: Adjust consumption tier limits based on workload
5. **Documentation**: Update deployment procedures for team reference
