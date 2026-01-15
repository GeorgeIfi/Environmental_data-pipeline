# Architecture Diagrams

## Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│                         AZURE CLOUD PLATFORM                               │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                    ORCHESTRATION LAYER                               │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────┐    │  │
│  │  │        Azure Data Factory (OrchestrationPipeline)         │    │  │
│  │  │                                                            │    │  │
│  │  │  [Blob Event Trigger] ──────┐                            │    │  │
│  │  │  [Schedule Trigger]          │                            │    │  │
│  │  │                              ▼                            │    │  │
│  │  │                         ┌──────────────┐                 │    │  │
│  │  │                         │ Web Activity │                 │    │  │
│  │  │                         │   1: Ingest  │                 │    │  │
│  │  │                         └──┬───────────┘                 │    │  │
│  │  │                            │ (POST)                     │    │  │
│  │  │                            ▼                            │    │  │
│  │  │                         ┌──────────────┐                 │    │  │
│  │  │                         │ Web Activity │                 │    │  │
│  │  │                         │  2: Transform│                 │    │  │
│  │  │                         └──┬───────────┘                 │    │  │
│  │  │                            │ (POST)                     │    │  │
│  │  │                            ▼                            │    │  │
│  │  │                         ┌──────────────┐                 │    │  │
│  │  │                         │ Web Activity │                 │    │  │
│  │  │                         │  3: Aggregate│                 │    │  │
│  │  │                         └──────────────┘                 │    │  │
│  │  │                                                            │    │  │
│  │  └────────────────────────────────────────────────────────────┘    │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │ │ │                                         │
│                              │ │ │                                         │
│                              ▼ ▼ ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                     PROCESSING LAYER                                 │  │
│  │                                                                      │  │
│  │  ┌─────────────────────────────────────────────────────────────┐   │  │
│  │  │           Azure Functions (Consumption Y1 Tier)            │   │  │
│  │  │                                                             │   │  │
│  │  │  ┌──────────────────┐  ┌──────────────────┐  ┌──────────┐ │   │  │
│  │  │  │   Function 1     │  │   Function 2     │  │Function 3│ │   │  │
│  │  │  │  Bronze Ingest   │  │ Silver Transform │  │Gold Agg  │ │   │  │
│  │  │  │                  │  │                  │  │          │ │   │  │
│  │  │  │ /api/bronze-ingest  /api/silver-trans  /api/gold-agg │   │  │
│  │  │  │                  │  │                  │  │          │ │   │  │
│  │  │  │ • Download CSV   │  │ • Read Bronze    │  │• Read    │ │   │  │
│  │  │  │ • Pandas ingest  │  │ • Validate data  │  │ Silver   │ │   │  │
│  │  │  │ • Upload Bronze  │  │ • Upload Silver  │  │• Groupby │ │   │  │
│  │  │  │   parquet        │  │   parquet        │  │• Upload  │ │   │  │
│  │  │  │                  │  │                  │  │  Gold    │ │   │  │
│  │  │  └──────────────────┘  └──────────────────┘  └──────────┘ │   │  │
│  │  │                                                             │   │  │
│  │  │  [Managed Identity] ──── Secure Auth to Storage           │   │  │
│  │  │  [Application Insights] ─ Monitoring & Tracing            │   │  │
│  │  │                                                             │   │  │
│  │  └─────────────────────────────────────────────────────────────┘   │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                              │ │ │                                         │
│                              ▼ ▼ ▼                                         │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                      STORAGE LAYER                                   │  │
│  │                                                                      │  │
│  │  ┌────────────────────────────────────────────────────────────┐    │  │
│  │  │          ADLS Gen2 - environmental-data Container          │    │  │
│  │  │                                                            │    │  │
│  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │    │  │
│  │  │  │    BRONZE    │  │    SILVER    │  │     GOLD     │    │    │  │
│  │  │  │              │  │              │  │              │    │    │  │
│  │  │  │ landing/     │  │ cleaned_data │  │analytics_data│    │    │  │
│  │  │  │ raw_data.csv │  │ .parquet     │  │.parquet      │    │    │  │
│  │  │  │              │  │              │  │              │    │    │  │
│  │  │  │ raw_data.    │  │ Validated &  │  │ Aggregated   │    │    │  │
│  │  │  │ parquet      │  │ deduplicated │  │ by date &    │    │    │  │
│  │  │  │              │  │              │  │ location     │    │    │  │
│  │  │  │ 2,174 rows   │  │ 2,174 rows   │  │ 2,174 rows   │    │    │  │
│  │  │  └──────────────┘  └──────────────┘  └──────────────┘    │    │  │
│  │  │                                                            │    │  │
│  │  │  Hierarchical Namespace enabled                          │    │  │
│  │  │  Parquet format with compression                         │    │  │
│  │  │  Full lineage tracking                                   │    │  │
│  │  │                                                            │    │  │
│  │  └────────────────────────────────────────────────────────────┘    │  │
│  │                                                                      │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Data Flow Diagram

```
┌──────────────────┐
│   CSV File       │
│   weather_raw    │
│   2,174 rows     │
└────────┬─────────┘
         │
         │ Upload to landing/
         ▼
┌──────────────────────────────────────────────────────────┐
│            Azure Storage (landing folder)                │
│                                                          │
│  weather_raw.csv                                         │
│  [2,174 rows]                                            │
└────────────┬─────────────────────────────────────────────┘
             │
             │ 1. Blob Created Event OR Manual Trigger
             ▼
    ┌────────────────────┐
    │  ADF Trigger       │
    │  (Event/Schedule)  │
    └─────────┬──────────┘
              │
              ▼
    ┌──────────────────────────────────────┐
    │  Web Activity 1: POST /bronze-ingest │
    │                                      │
    │  Function Body:                      │
    │  {                                   │
    │    "csv_file": "landing/..."         │
    │  }                                   │
    └────────────┬─────────────────────────┘
                 │
                 ▼
    ┌──────────────────────────────────────┐
    │   Function: bronze_ingestion()       │
    │   ├─ Download CSV from landing/      │
    │   ├─ Read with pd.read_csv()         │
    │   ├─ Standardize to Parquet          │
    │   └─ Upload to bronze/               │
    └────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│         Azure Storage (bronze folder)                    │
│                                                          │
│  raw_data.parquet                                        │
│  [2,174 rows, compressed]                                │
└──────────────┬───────────────────────────────────────────┘
               │
               │ 2. Web Activity 2: POST /silver-transform
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Function: bronze_to_silver()        │
    │   ├─ Download bronze parquet         │
    │   ├─ Remove nulls                    │
    │   ├─ Validate ranges                 │
    │   └─ Upload to silver/               │
    └────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│         Azure Storage (silver folder)                    │
│                                                          │
│  cleaned_data.parquet                                    │
│  [2,174 rows, validated]                                 │
└──────────────┬───────────────────────────────────────────┘
               │
               │ 3. Web Activity 3: POST /gold-transform
               │
               ▼
    ┌──────────────────────────────────────┐
    │  Function: silver_to_gold()          │
    │   ├─ Download silver parquet         │
    │   ├─ Groupby date & location         │
    │   ├─ Aggregate (mean/min/max/count)  │
    │   └─ Upload to gold/                 │
    └────────────┬─────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────────────┐
│         Azure Storage (gold folder)                      │
│                                                          │
│  analytics_data.parquet                                  │
│  [2,174 aggregates by date/location]                     │
│                                                          │
│  Ready for BI tools (Power BI, Tableau, etc)            │
└──────────────────────────────────────────────────────────┘
```

## Pandas Transformation Pipeline

```
Input CSV (bronze_ingestion)
         │
         ├─ pd.read_csv('landing/weather_raw.csv')
         │  └─ 2,174 rows, 8 columns
         │
         ▼
    ┌─────────────────────┐
    │   DataFrame Setup   │
    │   ├─ dtype: object  │
    │   ├─ index: RangeIndex
    │   └─ memory: ~1MB
    └──────────┬──────────┘
               │
               ▼
    ┌─────────────────────┐
    │   df.to_parquet()   │ ──→ bronze/raw_data.parquet
    │   compression: snappy
    └──────────┬──────────┘
               │
Bronze → Silver Transformation (bronze_to_silver)
               │
               ├─ pd.read_parquet('bronze/...')
               │
               ├─ df['measurement_time'] = pd.to_datetime(...)
               │  └─ Parse ISO 8601 timestamps
               │
               ├─ df = df.dropna()
               │  └─ Remove rows with missing values
               │
               ├─ Validation:
               │  ├─ df[df['latitude'].between(-90, 90)]
               │  ├─ df[df['longitude'].between(-180, 180)]
               │  └─ df[df['temperature'].between(-50, 50)]
               │
               ├─ df['date'] = df['measurement_time'].dt.date
               │
               ▼
    ┌─────────────────────┐
    │   df.to_parquet()   | ──→ silver/cleaned_data.parquet
    │   compression: snappy
    └──────────┬──────────┘
               │
Silver → Gold Transformation (silver_to_gold)
               │
               ├─ pd.read_parquet('silver/...')
               │
               ├─ df.groupby(['date', 'location_name']).agg({
               │    'temperature': ['mean', 'min', 'max', 'count'],
               │    'pressure': ['mean', 'min', 'max'],
               │    'humidity': ['mean', 'min', 'max'],
               │    'wind_speed': ['mean', 'max']
               │  })
               │  └─ 2,174 aggregations (daily per location)
               │
               ├─ Reset index for flat structure
               │
               ▼
    ┌─────────────────────┐
    │   df.to_parquet()   | ──→ gold/analytics_data.parquet
    │   compression: snappy
    └─────────────────────┘
               │
               ▼
    ┌─────────────────────┐
    │   Ready for BI      │
    │   - Power BI        │
    │   - Synapse SQL     │
    │   - Analytics tools │
    └─────────────────────┘
```

## Deployment Architecture

```
┌─────────────────────────────────────────────────────┐
│  Local Machine / CI Pipeline                        │
│                                                     │
│  ├─ .env (Azure credentials)                       │
│  ├─ Terraform code                                 │
│  ├─ Python functions                               │
│  ├─ Azure CLI tools                                │
│  └─ Git repository                                 │
│                                                     │
└────────────────┬────────────────────────────────────┘
                 │
                 │ terraform init
                 │ terraform plan
                 │ terraform apply
                 ▼
    ┌─────────────────────────────────┐
    │  Terraform State Management     │
    │  ├─ terraform.tfstate           │
    │  ├─ terraform.tfstate.backup    │
    │  └─ .terraform/ directory       │
    └──────────────┬────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Provisioned Azure Resources (30+)           │
    │                                              │
    │  Compute:                                    │
    │  ├─ Function App (func-...)                 │
    │  └─ App Service Plan (asp-...)              │
    │                                              │
    │  Storage:                                    │
    │  ├─ Data Lake (st...)                       │
    │  └─ Function Storage (stfunc-...)           │
    │                                              │
    │  Orchestration:                              │
    │  ├─ Data Factory (adf-...)                  │
    │  ├─ Linked Services                         │
    │  └─ Pipelines                               │
    │                                              │
    │  Monitoring:                                 │
    │  ├─ Application Insights (appins-...)       │
    │  └─ RBAC Roles                              │
    │                                              │
    │  Analytics:                                  │
    │  ├─ Synapse Workspace (syn-...)             │
    │  └─ Container Registry (acr-...)            │
    │                                              │
    └──────────────┬───────────────────────────────┘
                   │
                   │ ./deploy_functions.sh
                   │ ├─ Install azure-functions-core-tools
                   │ ├─ pip install -r requirements.txt
                   │ └─ func azure functionapp publish
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Functions Deployed to Azure                 │
    │                                              │
    │  ├─ bronze-ingest                           │
    │  ├─ silver-transform                        │
    │  └─ gold-transform                          │
    │                                              │
    │  URLs Active:                                │
    │  ├─ https://func-env.../api/bronze-ingest   │
    │  ├─ https://func-env.../api/silver-transform│
    │  └─ https://func-env.../api/gold-transform  │
    │                                              │
    └──────────────┬───────────────────────────────┘
                   │
                   │ Upload CSV to landing/
                   │ OR trigger ADF pipeline manually
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │  Pipeline Execution                          │
    │  ├─ Function 1: bronze-ingest (HTTP 200)    │
    │  ├─ Function 2: silver-transform (HTTP 200) │
    │  └─ Function 3: gold-transform (HTTP 200)   │
    │                                              │
    │  Data Flow:                                  │
    │  CSV → Bronze → Silver → Gold                │
    │                                              │
    │  Monitoring:                                 │
    │  ├─ ADF Monitor (pipeline runs)             │
    │  ├─ App Insights (function traces)          │
    │  └─ Azure Portal (logs)                     │
    │                                              │
    └──────────────────────────────────────────────┘
```

## Security Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                   SECURITY LAYERS                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 1: Identity & Access Control                │  │
│  │                                                     │  │
│  │  Service Principal (dbc12432-56e7-...)            │  │
│  │  └─ User Access Administrator role                │  │
│  │     ├─ Provision Terraform resources              │  │
│  │     └─ Manage RBAC assignments                    │  │
│  │                                                     │  │
│  │  Function App Managed Identity                    │  │
│  │  └─ Storage Blob Data Contributor role            │  │
│  │     ├─ Read blobs from landing/                   │  │
│  │     ├─ Write blobs to bronze/silver/gold/         │  │
│  │     └─ No hardcoded credentials needed            │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 2: Credential Management                    │  │
│  │                                                     │  │
│  │  .env File (Local, not in Git)                     │  │
│  │  └─ AZURE_SUBSCRIPTION_ID                         │  │
│  │  └─ AZURE_TENANT_ID                               │  │
│  │  └─ AZURE_CLIENT_ID                               │  │
│  │  └─ AZURE_CLIENT_SECRET                           │  │
│  │                                                     │  │
│  │  Function App Settings (Managed by Terraform)      │  │
│  │  └─ Data Lake connection via Managed Identity      │  │
│  │  └─ No storage keys in code                        │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 3: Network & Communication Security         │  │
│  │                                                     │  │
│  │  ADF → Functions (HTTPS only)                     │  │
│  │  └─ Function auth via Anonymous (auth built-in)   │  │
│  │  └─ TLS 1.2 minimum                               │  │
│  │                                                     │  │
│  │  Functions → Storage (Private Endpoint optional)   │  │
│  │  └─ Managed Identity prevents key exposure        │  │
│  │  └─ No connection strings in logs                 │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 4: Data Protection & Encryption             │  │
│  │                                                     │  │
│  │  Storage Encryption                               │  │
│  │  └─ Azure Storage Service Encryption (SSE)        │  │
│  │  └─ 256-bit AES encryption at rest                │  │
│  │                                                     │  │
│  │  Data Format                                       │  │
│  │  └─ Parquet with snappy compression               │  │
│  │  └─ Columnar format (enables selective access)    │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                        ▼                                   │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Layer 5: Audit & Monitoring                       │  │
│  │                                                     │  │
│  │  Azure Activity Log                                │  │
│  │  └─ All Terraform actions logged                   │  │
│  │  └─ RBAC changes tracked                           │  │
│  │                                                     │  │
│  │  Application Insights                              │  │
│  │  └─ Function execution traces                      │  │
│  │  └─ Exceptions and errors logged                  │  │
│  │  └─ Performance metrics collected                 │  │
│  │                                                     │  │
│  │  Storage Diagnostics                               │  │
│  │  └─ Read/Write operations logged                  │  │
│  │  └─ Access patterns tracked                        │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Cost Flow Diagram

```
Monthly Cost Breakdown (~$22-25/month for daily execution)

┌────────────────────────────────────────────────────────┐
│                                                        │
│  Daily CSV Processing Workload                        │
│  └─ 1 CSV file, ~2MB, 2,174 rows                     │
│  └─ Process: 1x per day at 2 AM UTC                  │
│                                                        │
└────────────────┬───────────────────────────────────────┘
                 │
                 ├────────────────────────────────────┐
                 │                                    │
                 ▼                                    ▼
    ┌─────────────────────┐         ┌──────────────────────┐
    │ Function Execution  │         │ Storage Operations   │
    │ Costs               │         │ Costs                │
    │                     │         │                      │
    │ • 3 invocations     │         │ • Read landing/ CSV  │
    │   per day           │         │   = ~$0.01/day       │
    │ • ~5 seconds each   │         │                      │
    │   (processing)      │         │ • Write to bronze/   │
    │ • First 1M free     │         │   silver/gold =      │
    │   per month         │         │   ~$0.01/day         │
    │ • $0.20 per million │         │                      │
    │   after free tier   │         │ Total: ~$0.02/day    │
    │ • Total: ~$0.20/day │         │ (~$0.60/month)       │
    │ (~$6/month)         │         │                      │
    │                     │         │                      │
    └─────────────────────┘         └──────────────────────┘
                 │                                    │
                 ├────────────────────────────────────┤
                 │                                    │
                 ▼                                    ▼
    ┌─────────────────────┐         ┌──────────────────────┐
    │ Data Factory Costs  │         │ Other Services       │
    │                     │         │                      │
    │ • Web Activity      │         │ • App Service Plan   │
    │   per execution     │         │   = ~$9/month        │
    │ • 3 activities      │         │   (Consumption tier) │
    │   per pipeline      │         │                      │
    │ • $0.50/day for     │         │ • Application        │
    │   3 activities      │         │   Insights           │
    │ • Total: ~$0.50/day │         │   = ~$5/month        │
    │ (~$15/month)        │         │                      │
    │                     │         │ Total: ~$14/month    │
    │                     │         │                      │
    └─────────────────────┘         └──────────────────────┘
                 │                                    │
                 └────────────────┬───────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │  Total Monthly Cost          │
                    │                              │
                    │  Functions:       ~$6        │
                    │  Storage:         ~$0.60     │
                    │  Data Factory:    ~$15       │
                    │  Other Services:  ~$14       │
                    │  ───────────────────────────  │
                    │  TOTAL:           ~$22-25    │
                    │                              │
                    │  Per-day cost:   ~$0.70      │
                    │                              │
                    └──────────────────────────────┘

Note: Costs are estimates based on:
- Daily CSV processing at 2 AM
- Free tier consumption minimized
- Consumption tier pricing
- No storage tiers or lifecycle policies
- No private endpoints or advanced networking
```

---

**For detailed explanations of each architecture component, see:**
- [ADF_ORCHESTRATION.md](ADF_ORCHESTRATION.md) - Phase-by-phase deployment
- [AZURE_FUNCTIONS_IMPLEMENTATION.md](AZURE_FUNCTIONS_IMPLEMENTATION.md) - Implementation details
- [README.md](README.md) - Overview and tech stack
- [azure_functions/README.md](azure_functions/README.md) - Function specifications
