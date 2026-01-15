# Deployment Checklist

**Project**: Environmental Data Engineering Pipeline (Azure-Native)
**Target**: Production Azure Environment
**Estimated Duration**: 30-45 minutes

---

## Pre-Deployment Verification

### Local Environment
- [ ] Python 3.10+ installed: `python3 --version`
- [ ] Azure CLI installed: `az --version`
- [ ] Terraform 1.7.0+ installed: `terraform --version`
- [ ] Git configured: `git config --global user.name` and `git config --global user.email`
- [ ] Current directory is project root: `ls README.md`

### Azure Credentials
- [ ] Logged in to Azure CLI: `az login`
- [ ] Subscription selected: `az account show`
- [ ] Service Principal credentials in `.env` file
- [ ] `.env` file NOT in git (verify: `git status .env` → untracked)
- [ ] Credentials are valid and have User Access Administrator role

### Data Files
- [ ] CSV file exists: `ls data/raw/weather_raw.csv`
- [ ] CSV contains weather data with expected columns
- [ ] CSV is readable: `head -5 data/raw/weather_raw.csv`

### Project Structure
- [ ] Azure Functions code exists: `ls azure_functions/bronze_ingestion/__init__.py`
- [ ] Terraform code exists: `ls infra/terraform/main.tf`
- [ ] Deploy script exists: `ls deploy_functions.sh`
- [ ] Documentation exists: `ls ADF_ORCHESTRATION.md`

---

## Phase 1: Infrastructure Deployment (20-30 minutes)

### Terraform Preparation
- [ ] Navigate to Terraform directory: `cd infra/terraform`
- [ ] Initialize Terraform: `terraform init`
  - Expected: `.terraform/` directory created
  - Expected: `.terraform.lock.hcl` file created
- [ ] Validate configuration: `terraform validate`
  - Expected: "Success! The configuration is valid..."
  - Note: Deprecation warnings are acceptable

### Terraform Plan Review
- [ ] Generate plan: `terraform plan`
  - Expected: Plan shows 30+ resources to be created
  - Expected: Function App resources (asp, function app, storage, insights, linked services, pipeline)
  - Expected: No errors or critical warnings
- [ ] Review plan carefully:
  - [ ] Correct resource group: `rg-envpipeline-dev`
  - [ ] Correct location: `uksouth`
  - [ ] Correct storage account naming: `stenvpipeline*`
  - [ ] Correct function app naming: `func-envpipeline-*`

### Terraform Apply
- [ ] Start infrastructure deployment: `terraform apply`
  - Expected duration: 20-30 minutes
  - Expected: Resources created in this order:
    1. Resource Group
    2. Storage Accounts (data lake + function storage)
    3. Data Factory + linked services + datasets
    4. Synapse Workspace
    5. Container Registry
    6. Function App (App Service Plan, Function App, Managed Identity, RBAC)
    7. Application Insights
    8. ADF Pipeline
- [ ] Monitor progress in terminal
- [ ] Address any errors:
  - [ ] If storage account name taken, Terraform will retry with different suffix
  - [ ] If quota exceeded, contact Azure support or delete old resources
  - [ ] If auth fails, re-run `az login`

### Terraform Post-Apply
- [ ] Confirm all resources created: `terraform apply` shows "Apply complete! Resources: XX added."
- [ ] Export outputs to JSON: `terraform output -json > outputs.json`
- [ ] Verify key outputs exist:
  - [ ] `storage_account_name`: Should be `stenvpipeline*`
  - [ ] `function_app_name`: Should be `func-envpipeline-*`
  - [ ] `function_app_endpoint`: Should be `https://func-envpipeline-*.azurewebsites.net`
  - [ ] `data_factory_name`: Should be `adf-environmental-*`

### Verify in Azure Portal
- [ ] Navigate to https://portal.azure.com
- [ ] Search for resource group: `rg-envpipeline-dev`
- [ ] Verify resources exist:
  - [ ] Storage account `stenvpipeline*`
  - [ ] Function App `func-envpipeline-*`
  - [ ] Data Factory `adf-environmental-*`
  - [ ] App Service Plan `asp-envpipeline-dev`
  - [ ] Application Insights `appins-envpipeline-functions`

---

## Phase 2: Function Deployment (5-10 minutes)

### Prepare Deployment
- [ ] Return to project root: `cd ../../..`
- [ ] Current directory is project root: `pwd` → `/workspaces/environmental-data-platform`
- [ ] Make script executable: `chmod +x deploy_functions.sh`
- [ ] Script is readable: `cat deploy_functions.sh | head -20`

### Execute Deployment
- [ ] Run deployment script: `./deploy_functions.sh`
  - Expected duration: 5-10 minutes
  - Expected: Script installs azure-functions-core-tools (if needed)
  - Expected: Script installs Python dependencies from requirements.txt
  - Expected: Script publishes functions to Azure
  - Expected output shows:
    ```
    ✓ Functions deployed successfully!
    ✓ Function endpoints:
      - Bronze Ingest: https://func-envpipeline-XXXX.azurewebsites.net/api/bronze-ingest
      - Silver Transform: https://func-envpipeline-XXXX.azurewebsites.net/api/silver-transform
      - Gold Transform: https://func-envpipeline-XXXX.azurewebsites.net/api/gold-transform
    ```

### Verify Function Deployment
- [ ] Functions appear in Azure Portal:
  - [ ] Go to Function App in portal
  - [ ] Left sidebar → Functions
  - [ ] Verify 3 functions listed:
    - [ ] `bronze-ingest`
    - [ ] `silver-transform`
    - [ ] `gold-transform`
- [ ] Each function has an endpoint URL
- [ ] Application Insights integration confirmed

### Check Function Logs
- [ ] View function app logs: `az functionapp log tail --name func-envpipeline-XXXX --resource-group rg-envpipeline-dev`
  - Expected: No errors, clean startup
  - Can press Ctrl+C to exit

---

## Phase 3: Data Preparation (5 minutes)

### Upload Test Data
- [ ] Extract storage credentials from Terraform outputs:
  ```bash
  STORAGE_ACCOUNT=$(terraform -chdir=infra/terraform output -raw storage_account_name)
  STORAGE_KEY=$(terraform -chdir=infra/terraform output -raw storage_account_key)
  echo "Storage: $STORAGE_ACCOUNT"
  echo "Key: ${STORAGE_KEY:0:10}..."  # Show first 10 chars only
  ```
- [ ] Verify storage account accessible:
  ```bash
  az storage container list --account-name $STORAGE_ACCOUNT --account-key "$STORAGE_KEY"
  ```
  - Expected: Shows `environmental-data` container

- [ ] Upload CSV to landing folder:
  ```bash
  az storage blob upload \
    --account-name $STORAGE_ACCOUNT \
    --account-key "$STORAGE_KEY" \
    --container-name environmental-data \
    --name landing/weather_raw.csv \
    --file data/raw/weather_raw.csv
  ```
  - Expected: "Upload succeeded"

- [ ] Verify upload:
  ```bash
  az storage blob list \
    --account-name $STORAGE_ACCOUNT \
    --account-key "$STORAGE_KEY" \
    --container-name environmental-data \
    --prefix landing/
  ```
  - Expected: Shows `weather_raw.csv` in landing folder

---

## Phase 4: Function Testing (5 minutes)

### Test Bronze Ingestion Function
- [ ] Extract endpoint:
  ```bash
  FUNC_ENDPOINT=$(terraform -chdir=infra/terraform output -raw function_app_endpoint)
  echo "Endpoint: $FUNC_ENDPOINT"
  ```

- [ ] Call bronze-ingest function:
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

- [ ] Expected response:
  ```json
  {
    "status": "success",
    "stage": "bronze_ingestion",
    "rows_ingested": 2174,
    "output_path": "https://stenvpipeline*.blob.core.windows.net/environmental-data/bronze/raw_data.parquet"
  }
  ```
  - [ ] Status is "success"
  - [ ] Rows ingested: 2174
  - [ ] Output path contains "bronze/"

### Test Silver Transformation Function
- [ ] Call silver-transform function:
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

- [ ] Expected response:
  ```json
  {
    "status": "success",
    "stage": "silver_transformation",
    "rows_cleaned": 2174,
    "output_path": "https://stenvpipeline*.blob.core.windows.net/environmental-data/silver/cleaned_data.parquet"
  }
  ```

### Test Gold Aggregation Function
- [ ] Call gold-transform function:
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

- [ ] Expected response:
  ```json
  {
    "status": "success",
    "stage": "gold_aggregation",
    "rows_aggregated": 2174,
    "output_path": "https://stenvpipeline*.blob.core.windows.net/environmental-data/gold/analytics_data.parquet"
  }
  ```

### Verify Output Files
- [ ] Check storage for all three parquet files:
  ```bash
  az storage blob list --account-name $STORAGE_ACCOUNT --account-key "$STORAGE_KEY" \
    --container-name environmental-data --prefix bronze/
  az storage blob list --account-name $STORAGE_ACCOUNT --account-key "$STORAGE_KEY" \
    --container-name environmental-data --prefix silver/
  az storage blob list --account-name $STORAGE_ACCOUNT --account-key "$STORAGE_KEY" \
    --container-name environmental-data --prefix gold/
  ```
  - [ ] bronze/raw_data.parquet exists
  - [ ] silver/cleaned_data.parquet exists
  - [ ] gold/analytics_data.parquet exists

---

## Phase 5: Data Factory Pipeline Orchestration (5 minutes)

### Manual Pipeline Trigger
- [ ] Navigate to Azure Portal
- [ ] Find Data Factory: Search for `adf-environmental-*`
- [ ] Open Data Factory Studio
- [ ] Go to Pipelines section
- [ ] Select `OrchestrationPipeline`
- [ ] Click "Trigger" → "Trigger Now"
- [ ] Review and confirm trigger

### Monitor Pipeline Execution
- [ ] Go to Monitor → Pipeline Runs
- [ ] Find your pipeline run (should be most recent)
- [ ] Click on the run to see activity details
- [ ] Verify all 3 activities succeeded:
  - [ ] BronzeIngestActivity: SUCCESS
  - [ ] SilverTransformActivity: SUCCESS
  - [ ] GoldTransformActivity: SUCCESS
- [ ] Each activity should show HTTP 200 response
- [ ] Check timing (should each complete within 30 seconds)

### View Activity Outputs
- [ ] For each activity, expand details:
  - [ ] Click on activity name
  - [ ] View Input and Output sections
  - [ ] Verify JSON response contains:
    - [ ] "status": "success"
    - [ ] Row count (should be 2174 for bronze/silver, 2174 aggregates for gold)
    - [ ] Output blob path

---

## Phase 6: Monitoring & Observability (5 minutes)

### Application Insights
- [ ] Navigate to Application Insights resource in portal
  - Name: `appins-envpipeline-functions`
- [ ] Go to Traces section
- [ ] Filter by time range (last hour)
- [ ] Verify function execution traces appear:
  - [ ] bronze-ingest invocation logged
  - [ ] silver-transform invocation logged
  - [ ] gold-transform invocation logged
- [ ] Go to Metrics section
- [ ] View function invocation counts:
  - [ ] Should see 3 invocations per function
  - [ ] Response times should be visible

### Function App Logs
- [ ] View logs via Azure CLI:
  ```bash
  az functionapp log tail --name func-envpipeline-XXXX --resource-group rg-envpipeline-dev
  ```
- [ ] Should see successful function invocations:
  - [ ] "Finished HTTP request" messages
  - [ ] No error messages
  - [ ] Status code 200 for all requests

### Data Factory Monitor
- [ ] In Data Factory, go to Monitor
- [ ] Pipeline runs history visible
- [ ] Pipeline run details show:
  - [ ] Duration of pipeline execution
  - [ ] Duration of each activity
  - [ ] Status: All activities succeeded

---

## Phase 7: Post-Deployment Verification

### Cost Verification
- [ ] Check Azure Cost Management (if available)
  - [ ] Resource group: `rg-envpipeline-dev`
  - [ ] Verify costs align with estimates (~$22/month)
  - [ ] Check breakdown by resource type

### Documentation Review
- [ ] All expected documentation files present:
  - [ ] ADF_ORCHESTRATION.md
  - [ ] AZURE_FUNCTIONS_IMPLEMENTATION.md
  - [ ] QUICK_REFERENCE.md
  - [ ] ARCHITECTURE_DIAGRAMS.md
  - [ ] PROJECT_STATUS.md
  - [ ] azure_functions/README.md
  - [ ] Updated README.md

### Git History
- [ ] All commits present with meaningful messages
- [ ] No uncommitted changes: `git status` shows clean
- [ ] Latest commits include Azure Functions work

---

## Troubleshooting Checklist

### If Terraform Apply Fails
- [ ] Check credentials: `az account show`
- [ ] Verify subscription has quota for resources
- [ ] Check if resource names already exist (suffix should randomize)
- [ ] Run `terraform destroy` and retry if necessary
- [ ] Check internet connectivity and Azure service status

### If Function Deployment Fails
- [ ] Ensure Azure CLI logged in: `az login`
- [ ] Check Azure Functions Core Tools installed: `func --version`
- [ ] Verify Python 3.10+: `python3 --version`
- [ ] Check requirements.txt dependencies installable: `pip install -r azure_functions/requirements.txt`

### If CSV Upload Fails
- [ ] Verify storage account name: `terraform output storage_account_name`
- [ ] Verify storage key: `terraform output storage_account_key`
- [ ] Ensure container exists: `az storage container list --account-name $STORAGE_ACCOUNT`
- [ ] Check CSV file readable: `file data/raw/weather_raw.csv`

### If Function Tests Fail
- [ ] Check function logs: `az functionapp log tail --name func-envpipeline-XXXX ...`
- [ ] Verify function endpoint URL is correct
- [ ] Ensure storage credentials passed in request body
- [ ] Check Application Insights for error traces
- [ ] Test with simpler curl request first (check auth only)

### If Pipeline Doesn't Trigger
- [ ] Verify pipeline created: Go to Data Factory → Pipelines
- [ ] Check ADF linked services configured correctly
- [ ] Verify web activities have correct function URLs
- [ ] Check ADF Monitor for error messages
- [ ] Verify trigger is activated (blob event or schedule)

---

## Sign-Off Checklist

### Deployment Complete When:
- [ ] All Terraform resources created (verified in Azure Portal)
- [ ] All 3 functions deployed and callable
- [ ] CSV file uploaded to landing/ folder
- [ ] All 3 function tests return HTTP 200 with correct data
- [ ] Parquet files appear in bronze/, silver/, and gold/ folders
- [ ] ADF pipeline execution succeeds with all 3 activities
- [ ] Application Insights shows execution traces
- [ ] All documentation reviewed and understood
- [ ] Cost is within expected range (~$22/month)

### Deployment Issues Resolved:
- [ ] No critical errors in logs
- [ ] No unresolved blockers
- [ ] All monitoring working correctly
- [ ] Rollback plan documented (terraform destroy)

---

## Post-Deployment Actions

### Day 1
- [ ] Review Azure Portal dashboards
- [ ] Test accessing data in Power BI (optional)
- [ ] Share documentation with team

### Week 1
- [ ] Configure scheduled trigger (daily execution)
- [ ] Set up cost alerts
- [ ] Document operational procedures

### Month 1
- [ ] Review usage patterns and optimize
- [ ] Consider moving to Premium tier if cold starts problematic
- [ ] Plan data retention and lifecycle policies

---

## Support & Escalation

**Questions About**: **Reference**
Deployment steps | ADF_ORCHESTRATION.md (Phase 1-2)
Function specifications | azure_functions/README.md
Quick commands | QUICK_REFERENCE.md
Architecture | ARCHITECTURE_DIAGRAMS.md
Implementation details | AZURE_FUNCTIONS_IMPLEMENTATION.md
Project status | PROJECT_STATUS.md

---

## Final Notes

- **Backup your .env file** (contains secrets, not in git)
- **Save terraform.tfstate file** (IaC state, needed for updates)
- **Keep backup of Azure credentials**
- **Review Azure subscription bills monthly**
- **Document any manual changes made in portal**

**Estimated Total Time**: 30-45 minutes from start to full deployment ✅

---

**Status After Completion**: ✅ PRODUCTION DEPLOYMENT COMPLETE

The environmental data ETL pipeline is now fully operational in Azure.
All data flows through the medallion architecture (Bronze → Silver → Gold).
Monitor via Application Insights and Azure Data Factory Monitor panels.
