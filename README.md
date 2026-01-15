# Environmental Data Engineering Pipeline (Azure-Native ETL)

## Overview

This project implements a **fully Azure-native**, serverless ETL pipeline for environmental data processing. The architecture follows the **medallion pattern** (Bronze → Silver → Gold) with orchestration via Azure Data Factory and processing via Azure Functions.

### Key Features

- **Cloud-Native Architecture**: 100% Azure-hosted, serverless compute (no VMs)
- **Azure Functions**: 3 HTTP-triggered functions for medallion layer processing
- **Infrastructure as Code**: Terraform-managed infrastructure (22 Azure resources, validated for duplicates)
- **Azure Data Factory**: Orchestration pipeline using WebActivity to invoke Functions
- **Production-Ready**: RBAC, Managed Identities, monitoring via Application Insights
- **Data Quality**: Validation and cleansing in Silver layer, aggregations in Gold layer
- **Scalable Storage**: ADLS Gen2 with medallion architecture for data governance
- **Cost Optimized**: Consumption tier pricing for Functions (pay-per-execution)
- **Comprehensive Testing**: 36 unit tests with 100% pass rate via Pytest
- **Failure Handling**: 12 documented failure patterns with automated alerting via Azure Monitor
- **Business Analytics**: 50+ production-ready Synapse SQL queries for business intelligence
- **Full Documentation**: 11 markdown guides covering all aspects from deployment to analytics

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│            Azure Data Factory (orchestration_pipeline)         │
│                    WebActivity-based Pipeline                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BronzeIngestActivity → SilverTransformActivity → GoldTransActivity
│  (POST to /api/*)    (POST to /api/*)         (POST to /api/*)│
└───────────────────┬──────────────────┬──────────────────┬──────┘
                    │                  │                  │
                    ▼                  ▼                  ▼
    ┌─────────────────────────────────────────────────────────────┐
    │         Azure Functions (Consumption Y1 Tier)              │
    │          HTTP-Triggered, Managed Identity Auth             │
    │                                                             │
    │  Function 1: bronze-ingest (CSV → Parquet)               │
    │  Function 2: silver-transform (Validation & Cleaning)    │
    │  Function 3: gold-transform (Aggregation & Analytics)    │
    │                                                             │
    │  Runtime: Python 3.10 | Storage: Pandas DataFrames       │
    │  Monitoring: Application Insights (automatic)             │
    └─────────────────────┬─────────────────────────────────────┘
                          │
                          ▼
    ┌─────────────────────────────────────────────────────────────┐
    │        ADLS Gen2 Storage (Data Lake)                        │
    │       Managed Identity–based Access Control                │
    │                                                             │
    │  landing/ → bronze/ → silver/ → gold/                      │
    │  (CSV)      (Parquet) (Clean) (Analytics)                  │
    │                                                             │
    │  Filesystem: environmental-data                            │
    │  Format: CSV (landing) / Parquet (bronze, silver, gold)   │
    │  Compression: Snappy (reduce storage & I/O)              │
    └─────────────────────────────────────────────────────────────┘

    Additional Resources:
    ├─ Synapse Workspace (SQL analytics on gold layer)
    ├─ Container Registry (future Docker images)
    └─ App Service Plan (Functions host)
```

## Quick Start

### Prerequisites
- Azure CLI (`az login`)
- Terraform 1.7.0+
- Python 3.10+
- `.env` file with Azure credentials (subscription_id, tenant_id, client_id, client_secret)

### 1. Validate Infrastructure
```bash
cd infra/terraform
terraform init
terraform validate  # Verify configuration (no duplicates)
terraform plan      # Preview resources to be created
```

### 2. Deploy Infrastructure to Azure
```bash
terraform apply     # Deploy 22 Azure resources
```

### 3. Deploy Azure Functions
The Functions code is in `src/` (bronze_ingestion, silver_transformation, gold_transformation).
See [AZURE_FUNCTIONS_IMPLEMENTATION.md](AZURE_FUNCTIONS_IMPLEMENTATION.md) for deployment steps.

```bash
# Functions are Python 3.10-based, deployed to Function App via:
# - Azure Functions Core Tools, or
# - Direct zip deployment, or
# - GitHub Actions CI/CD pipeline
```

### 4. Test the Orchestration Pipeline
```bash
# Option A: Manual trigger via Azure Portal
# Navigate to Data Factory → orchestration_pipeline → Trigger now

# Option B: Programmatic trigger (requires authentication)
az datafactory pipeline create-run \
  --factory-name adf-environmental-<suffix> \
  --name orchestration_pipeline \
  --resource-group rg-envpipeline-dev
```

### 5. Monitor Execution
```bash
# Application Insights: Function traces and performance metrics
# Data Factory: Pipeline run history and activity logs
# ADLS Gen2: Validate data movement through medallion layers
```

---

## Cloud Mapping (Azure Services)

| Layer / Component | Azure Service | Purpose |
|-------------------|---------------|---------|
| **Storage** | ADLS Gen2 | Data lake with hierarchical namespace |
| **Bronze Layer** | ADLS Gen2 containers | Raw CSV landing, standardized Parquet |
| **Silver Layer** | ADLS Gen2 containers | Cleaned, validated, deduplicated data |
| **Gold Layer** | ADLS Gen2 containers | Aggregated, analytics-ready datasets |
| **Processing** | Azure Functions | HTTP-triggered, serverless ETL execution (3 functions) |
| **Orchestration** | Azure Data Factory | WebActivity pipeline coordination to Functions |
| **Identity** | Managed Identity | Secure, credential-less Function authentication |
| **Monitoring** | Application Insights | Function performance, logs, traces |
| **Analytics** | Synapse Workspace | SQL analytics on Gold layer data |
| **Infrastructure** | Terraform | 22 Azure resources, no duplicates, IaC-managed |

---

## Cost & Lifecycle Management

### Consumption Tier Benefits
- **Pay-per-execution**: Only charged when Functions run (first 1M executions/month free)
- **Auto-scaling**: Automatic scale-out under concurrent load
- **No minimum**: $0 cost when idle
- **Suitable for**: Intermittent or batch workloads

### Data Retention Strategy
- **Bronze**: Short retention (raw ingestion artifacts, 30-90 days)
- **Silver**: Medium retention (validated, deduplicated, 90-180 days)
- **Gold**: Long retention (production analytics, 1+ years)

### Cost Estimation
Assuming 2,174 row CSV processed daily:
- **Function executions**: ~$0.20/day (3 × invocations, within free tier)
- **Storage (ADLS Gen2)**: ~$0.02/day (read operations + storage)
- **Data Factory**: ~$0.50/day (web activity executions)
- **Application Insights**: ~$0.05/day (data ingestion)
- **Total**: ~$0.77/day (~$23/month)

*Note: Pricing assumes standard ADLS Gen2 read/write rates and uksouth region. Actual costs may vary.*

---

## Documentation

### Core Documentation
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Step-by-step infrastructure deployment
- [TRANSFORMATION_VALIDATION.md](TRANSFORMATION_VALIDATION.md) - Data quality validation logic
- [AZURE_FUNCTIONS_IMPLEMENTATION.md](AZURE_FUNCTIONS_IMPLEMENTATION.md) - Complete Azure Functions code and deployment guide

### Testing & Quality Assurance
- [TESTING.md](TESTING.md) - Comprehensive unit test suite (36 tests, 100% pass rate, Pytest)
- [tests/](tests/) - Test fixtures, ingestion tests, transformation tests, aggregation tests

### Monitoring & Failure Handling
- [ADF_FAILURE_HANDLING.md](ADF_FAILURE_HANDLING.md) - 12 documented failure patterns for ADF pipelines
- [ADF_FAILURE_HANDLING_PRACTICAL.md](ADF_FAILURE_HANDLING_PRACTICAL.md) - Step-by-step implementation guide
- [infra/terraform/adf_alerts.tf](infra/terraform/adf_alerts.tf) - Terraform configuration for Azure Monitor alerts

### Business Intelligence & Analytics
- [SYNAPSE_BUSINESS_QUERIES.md](SYNAPSE_BUSINESS_QUERIES.md) - Complete guide to using 50+ Synapse SQL queries
- [sql/06_business_analytics.sql](sql/06_business_analytics.sql) - 8 categories of business analytics queries (data quality, pollution analysis, location analysis, compliance, forecasting)
- [sql/](sql/) - Additional SQL scripts for regulatory compliance, trend analysis, spatial analysis, data quality

### Infrastructure & Code
- [infra/terraform/](infra/terraform/) - Infrastructure as Code (22 validated Azure resources, no duplicates)
- [src/](src/) - Python transformation code (Pandas-based, 3 Azure Functions)

---

## Testing & Quality Assurance

The pipeline includes a **comprehensive test suite** with 36 unit tests achieving 100% pass rate in 2.12 seconds.

### Test Coverage

| Component | Tests | Coverage |
|-----------|-------|----------|
| CSV Ingestion (bronze_ingest) | 9 tests | Format validation, compression, metadata |
| Bronze-to-Silver Transform | 13 tests | Data cleaning, validation, coordinate checks |
| Silver-to-Gold Aggregation | 14 tests | Grouping, sorting, accuracy validation |
| **Total** | **36 tests** | **100% pass rate** |

### Test Execution

```bash
python -m pytest tests/ -v
# Result: 36 passed in 2.12s ✅
```

All tests are fixture-based using `pytest`, enabling rapid iteration and comprehensive edge-case coverage without requiring Azure credentials.

See [TESTING.md](TESTING.md) for detailed test documentation and examples.

---

## Business Intelligence & Analytics (Synapse SQL)

The pipeline includes **50+ production-ready SQL queries** for Synapse Analytics covering 8 business intelligence categories:

### Query Categories

| Category | Queries | Business Value |
|----------|---------|-----------------|
| **Data Quality Checks** | 3 | Data governance, pipeline validation |
| **Pollution Analysis** | 4 | Health reporting, trend monitoring |
| **Location Analysis** | 3 | Urban planning, resource allocation |
| **Statistical Analysis** | 2 | Anomaly detection, quality control |
| **Time-Based Analysis** | 3 | Pattern recognition, policy evaluation |
| **Compliance & Regulatory** | 2 | Legal compliance, audit reports |
| **Predictive Prep** | 2 | Forecasting setup, ML model training |
| **Executive Dashboard** | 2 | Stakeholder reporting, KPI tracking |

### Quick Start: Run Business Queries

```sql
-- Query: Current pollution levels by location (real-time dashboard)
SELECT location, pollutant_type, avg_value, 
       CASE WHEN avg_value > 35.4 THEN 'UNHEALTHY' ELSE 'HEALTHY' END AS Status
FROM gold_weather
WHERE date = (SELECT MAX(date) FROM gold_weather)
ORDER BY location;

-- Query: 7-Day pollution trend
SELECT location, pollutant_type, date, avg_value
FROM gold_weather
WHERE date >= DATEADD(DAY, -7, CAST(GETDATE() AS DATE))
ORDER BY location, date DESC;
```

See [sql/06_business_analytics.sql](sql/06_business_analytics.sql) for all 50+ queries and [SYNAPSE_BUSINESS_QUERIES.md](SYNAPSE_BUSINESS_QUERIES.md) for complete business guide with real-world examples.

---

## Failure Handling & Monitoring

The pipeline includes **12 documented failure patterns** with automated alerting via Azure Monitor.

### Failure Handling Patterns

- ✅ Retry policies (exponential backoff, max retries)
- ✅ Failed run notifications (email, Slack)
- ✅ Circuit breaker pattern (prevent cascading failures)
- ✅ Dead letter queue (capture failed data)
- ✅ Monitoring alerts (pipeline/activity failures)
- ✅ Log Analytics tracking (centralized logging)
- ✅ Application Insights instrumentation (Function metrics)

### Alert Configuration (Terraform)

The [adf_alerts.tf](infra/terraform/adf_alerts.tf) automatically configures:
- **Action Group**: Email/Slack notification recipients
- **Metric Alerts**: Triggers on pipeline/activity failures
- **Log Analytics**: 30-day log retention for auditing
- **Smart Detection**: Anomaly-based alerting via Application Insights

```bash
# Update variables before terraform apply
alert_email_address = "your-team@company.com"
enable_detailed_monitoring = true
```

See [ADF_FAILURE_HANDLING.md](ADF_FAILURE_HANDLING.md) and [ADF_FAILURE_HANDLING_PRACTICAL.md](ADF_FAILURE_HANDLING_PRACTICAL.md) for complete documentation.

---

| Mode | Purpose | Environment | Trigger | Pipeline |
|------|---------|-------------|---------|----------|
| **Local** | Development, testing, CI | Local machine | Manual execution | N/A |
| **Cloud - Manual** | Testing, validation | Azure | Manual ADF trigger | `orchestration_pipeline` (WebActivity) |
| **Cloud - Event** | Production | Azure | Blob upload to landing/ | *(Currently manual only; configure blob triggers in ADF)* |

---

## Tech Stack

- **Language**: Python 3.10+
- **ETL Framework**: Pandas 2.0+ (efficient, single-machine processing)
- **Cloud Compute**: Azure Functions (serverless, consumption-based)
- **Orchestration**: Azure Data Factory (pipeline scheduling, monitoring)
- **Storage**: ADLS Gen2 (distributed file system, hierarchical namespace)
- **Infrastructure**: Terraform 1.7.0 (Azure resource management)
- **Monitoring**: Application Insights (distributed tracing, metrics)
- **Testing**: Pytest (data quality, transformation validation)
- **Identity**: Azure Managed Identity (secure, credential-less auth)

---

## Repository Structure

```
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── variables.tf
│       ├── data_factory.tf
│       └── outputs.tf
│
├── src/
│   ├── ingestion/
│   ├── transformations/
│   ├── orchestration/
│   │   └── adf_pipeline.py
│   ├── quality/
│   └── utils/
│
├── tests/
├── data/ (runtime only, not committed)
├── run_pipeline.py
├── requirements.txt
├── .env.example
└── README.md
```

---

## Data Quality & Validation

Data quality is treated as a **first-class concern**.

Implemented checks include:

- Null and completeness validation
- Required column enforcement
- Date parsing validation
- Aggregation sanity checks

Quality checks are:

- Embedded within transformation stages
- Enforced via `pytest` in CI
- Designed to **fail fast** to prevent downstream data corruption

---

## Configuration & Secrets Management

- No secrets or credentials are hard-coded
- Local development uses environment variables (`.env`, ignored)
- CI/CD injects secrets securely via GitHub Actions
- `.env.example` documents required variables without exposing values

---

## CI/CD Strategy

# CI (Tests + Validation):

- Dependency resolution

- Linting & unit tests

- Data quality tests (pytest)

- Temporary filesystem paths for reproducibility

- No cloud credentials required

# CD (Infra + Deployment):

Terraform plan/apply for Azure

RBAC + Synapse + ADLS provisioning

ADF orchestration deployment

CI and CD are intentionally decoupled to reflect real production constraints.

This separation mirrors real-world production pipelines and prevents unsafe deployments.

### Parameterised Paths (No Hard-Coded Data Locations)

All pipeline stages are fully parameterised:

- No stage assumes fixed directories such as `data/bronze` or `data/silver`
- Paths are passed explicitly between pipeline stages
- Configuration is controlled via:
  - CLI arguments (`run_pipeline.py`)
  - Environment variables (`RAW_DATA_PATH`, `BRONZE_DIR`, `SILVER_DIR`, `GOLD_DIR`)

This enables:

- Portable CI execution using temporary directories
- Safe re-runs without overwriting data
- Easy promotion between environments

### CI-Safe External Integrations

External cloud integrations are **disabled by default in CI**:

- Azure Data Lake uploads can be toggled off
- Synapse external table creation is optional
- Tests never require Azure credentials

This ensures CI pipelines remain fast, deterministic, and reliable.

### Test Strategy

Tests are written to be environment-agnostic:

- No dependency on committed data files
- Temporary paths via `pytest tmp_path`
- Positive and negative test cases, including:
  - Missing input files
  - Empty datasets
  - Schema violations

---

## Design Principles Demonstrated

- Separation of concerns
- Cloud-first, but locally runnable
- Config-driven execution
- Defensive data engineering
- Infrastructure as Code
- CI-first development mindset

---

## Author

**George Ifi**  
Data Engineer | Environmental Management MSc  
Focused on cloud-native data platforms and environmental technology
