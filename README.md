# Environmental Data Engineering Pipeline (Azure-Native ETL)

## Overview

This project implements a **fully Azure-native**, cloud-orchestrated environmental data engineering pipeline. The architecture follows the **medallion pattern** (Bronze → Silver → Gold) with orchestration via Azure Data Factory and processing via Azure Functions.

### Key Features

- **Cloud-Native Architecture**: 100% Azure-hosted, no local compute required
- **Serverless Processing**: Azure Functions with Consumption tier pricing
- **Infrastructure as Code**: Terraform-managed resources (30+ Azure components)
- **Automated Orchestration**: Azure Data Factory pipelines with event-driven triggers
- **Production-Ready**: RBAC, Managed Identities, monitoring via Application Insights
- **Data Quality**: Validation and cleansing in Silver layer, aggregations in Gold
- **Scalable Storage**: ADLS Gen2 with medallion architecture for data governance

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│              Azure Data Factory (Orchestration)              │
├──────────────────────────────────────────────────────────────┤
│   Web Activity                Web Activity        Web Activity│
│   (Bronze Ingest)     →    (Silver Transform)   → (Gold Agg) │
└──────────┬─────────────────────────┬──────────────────┬──────┘
           │                         │                  │
           ▼                         ▼                  ▼
    ┌────────────────────────────────────────────────────────┐
    │         Azure Functions (Consumption Tier)            │
    │                                                        │
    │  • bronze-ingest (CSV → Parquet)                      │
    │  • silver-transform (Cleaning & Validation)           │
    │  • gold-transform (Aggregation & Analytics)           │
    │                                                        │
    │  All functions handle Azure Storage operations        │
    │  Managed Identity provides secure authentication       │
    └────────────┬───────────────────────────────────────────┘
                 │
                 ▼
    ┌────────────────────────────────────────────────────────┐
    │        ADLS Gen2 Storage (Data Lake)                  │
    │                                                        │
    │  landing/  →  bronze/  →  silver/  →  gold/          │
    │                                                        │
    │  • Raw CSV ingestion                                  │
    │  • Parquet format (compression, schema)               │
    │  • Row-level lineage tracking                         │
    │  • Data governance via containers                     │
    └────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Azure CLI (`az login`)
- Terraform 1.7.0+
- Python 3.10+
- `.env` file with Azure credentials

### 1. Deploy Infrastructure
```bash
cd infra/terraform
terraform init
terraform plan
terraform apply
```

### 2. Deploy Azure Functions
```bash
chmod +x deploy_functions.sh
./deploy_functions.sh
```

### 3. Trigger Pipeline Manually
```bash
# Get function endpoint
FUNC_ENDPOINT=$(terraform -chdir=infra/terraform output -raw function_app_endpoint)
STORAGE_ACCOUNT=$(terraform -chdir=infra/terraform output -raw storage_account_name)
STORAGE_KEY=$(terraform -chdir=infra/terraform output -raw storage_account_key)

# Test bronze ingestion (upload CSV first to landing/)
curl -X POST "${FUNC_ENDPOINT}/api/bronze-ingest" \
  -H "Content-Type: application/json" \
  -d "{
    \"storage_account\": \"${STORAGE_ACCOUNT}\",
    \"storage_key\": \"${STORAGE_KEY}\",
    \"container\": \"environmental-data\",
    \"csv_file\": \"landing/weather_raw.csv\"
  }"
```

### 4. Configure Automated Triggers
See [ADF_ORCHESTRATION.md](ADF_ORCHESTRATION.md) for scheduling and event-driven triggers.

---

## Cloud Mapping (Azure Services)

| Layer / Component | Azure Service | Purpose |
|-------------------|---------------|---------|
| **Storage** | ADLS Gen2 | Data lake with hierarchical namespace |
| **Bronze Layer** | ADLS Gen2 containers | Raw CSV landing, standardized Parquet |
| **Silver Layer** | ADLS Gen2 containers | Cleaned, validated, deduplicated data |
| **Gold Layer** | ADLS Gen2 containers | Aggregated, analytics-ready datasets |
| **Processing** | Azure Functions | HTTP-triggered, serverless ETL execution |
| **Orchestration** | Azure Data Factory | Pipeline coordination, triggering, monitoring |
| **Identity** | Managed Identity | Secure, credential-less authentication |
| **Monitoring** | Application Insights | Function performance, logs, traces |
| **Infrastructure** | Terraform | 30+ Azure resources, IaC-managed |

---

## Cost & Lifecycle Management

### Storage Tiering
- **Bronze**: Short retention (raw ingestion artifacts)
- **Silver**: Medium retention (validated, deduplicated)
- **Gold**: Long retention (production analytics)

### Consumption Tier Benefits
- **Pay-per-execution**: Only charged when functions run
- **Auto-scaling**: Automatic scale-out under load
- **No minimum**: $0 cost when idle
- **Suitable for**: Intermittent or variable workloads

### Cost Estimation
Assuming 2,174 row CSV processed daily:
- **Function executions**: ~$0.20/day (3 × 1M free executions/month)
- **Storage**: ~$0.02/day (ADLS Gen2 read operations)
- **Data Factory**: ~$0.50/day (web activity costs)
- **Total**: ~$0.72/day (~$22/month)

---

## Documentation

- [ADF_ORCHESTRATION.md](ADF_ORCHESTRATION.md) - Complete deployment and execution guide
- [azure_functions/README.md](azure_functions/README.md) - Function details and local testing
- [TRANSFORMATION_VALIDATION.md](TRANSFORMATION_VALIDATION.md) - Data quality validation logic
- [infra/terraform/](infra/terraform/) - Infrastructure as Code

---

## Mode of Operation

| Mode | Purpose | Environment | Trigger |
|------|---------|-------------|---------|
| **Local** | Development, testing, CI | Local machine | Manual execution |
| **Cloud - Manual** | Testing, validation | Azure | Manual ADF trigger |
| **Cloud - Event** | Production | Azure | Blob upload to landing/ |
| **Cloud - Scheduled** | Regular batches | Azure | Daily/hourly ADF schedule |

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
