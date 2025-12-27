# Environmental Data Engineering Pipeline (Azure-centric)

## Overview

This project implements an end-to-end **environmental data engineering pipeline** designed using cloud-native and production-grade data engineering principles. While Azure is the primary target platform, the pipeline is fully runnable **locally and in CI**, making it suitable for development, testing, and portfolio demonstration.

The pipeline follows the **medallion architecture** (Raw → Bronze → Silver → Gold) and emphasizes:

- Infrastructure as Code (IaC)
- Parameterised, config-driven execution
- Strong data quality enforcement
- CI-safe, reproducible workflows

---

## Architecture

```
┌──────────┐
│  Source  │  (CSV / External data)
└────┬─────┘
     │
     ▼
┌──────────┐
│   Raw    │  Immutable landing zone
└────┬─────┘
     ▼
┌──────────┐
│  Bronze  │  Standardisation & basic cleaning
└────┬─────┘
     ▼
┌──────────┐
│  Silver  │  Validated, enriched datasets
└────┬─────┘
     ▼
┌──────────┐
│   Gold   │  Curated aggregates for analytics
└──────────┘
```

---

## Cloud Mapping (Azure-oriented)

| Pipeline Layer | Azure Service |
|---------------|--------------|
| Raw / Bronze / Silver / Gold | Azure Data Lake Storage Gen2 |
| Orchestration | Apache Airflow |
| Infrastructure | Terraform |
| CI | GitHub Actions |

---

## Tech Stack

- Python 3.11
- Pandas
- Pytest
- Apache Airflow
- Terraform (Azure)
- Azure Data Lake Storage Gen2
- GitHub Actions

---

## Repository Structure

```
.
├── infra/
│   └── terraform/
│       ├── main.tf
│       ├── data_factory.tf
│       └── variables.tf
│
├── src/
│   ├── ingestion/
│   │   └── ingest_csv.py
│   ├── transformations/
│   │   ├── bronze_to_silver.py
│   │   └── silver_to_gold.py
│   ├── orchestration/
│   │   └── airflow_dag.py
│   ├── quality/
│   │   └── data_quality_checks.py
│   └── utils/
│       ├── azure_storage.py
│       └── synapse_client.py
│
├── data/              # runtime-only, ignored by Git
│   ├── raw/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── tests/
│   ├── test_ingestion.py
│   └── test_quality.py
│
├── run_pipeline.py
├── requirements.txt
├── .gitignore
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

## CI/CD Considerations

### CI vs CD Separation

- **Continuous Integration (CI)** is responsible for:
  - Dependency installation
  - Static validation
  - Unit and data quality tests
  - Fast failure on schema or completeness issues

- **Continuous Deployment (CD)** is intentionally decoupled and would only run **after CI passes**, handling:
  - Terraform-based infrastructure provisioning
  - Cloud resource configuration
  - Platform-level deployments

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
