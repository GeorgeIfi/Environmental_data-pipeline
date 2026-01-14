# Environmental Data Engineering Pipeline (Azure-centric)

## Overview

This project implements an end-to-end environmental data engineering pipeline using modern data engineering patterns and cloud-native services. The architecture is suitable for:

Portfolio demonstration (storytelling to employers)

Cloud engineering learning (Terraform + Azure + CI/CD)

Production pathway (lifecycle, RBAC, orchestration, separation of concerns)

The pipeline follows the medallion architecture (Bronze → Silver → Gold) with an emphasis on:

- Infrastructure as Code (Terraform)

- Config-driven and parameterised execution

- Data quality as a first-class construct

- CI-safe workflows

- Cost-aware and lifecycle-aware storage design

---

## Architecture

```
┌──────────┐
│  Source  │  (CSV / External APIs / Weather feeds)
└────┬─────┘
     │
     ▼
┌──────────┐
│  Bronze  │  Landing & standardisation
└────┬─────┘
     ▼
┌──────────┐
│  Silver  │  Validation & enrichment
└────┬─────┘
     ▼
┌──────────┐
│   Gold   │  Curated analytical outputs
└──────────┘

```

---

## Cloud Mapping (Azure-oriented)

| Layer / Concern      | Azure Service                 |
| -------------------- | ----------------------------- |
| Bronze/Silver/Gold   | ADLS Gen2                     |
| Compute / Query      | Synapse Serverless SQL        |
| Orchestration        | Azure Data Factory            |
| Identity & Access    | Managed Identity + RBAC       |
| Infrastructure (IaC) | Terraform                     |
| CI                   | GitHub Actions                |


---
## Cost & Lifecycle Awareness

Cloud storage and analytics workloads grow over time. Lifecycle rules and cost controls are implemented as part of IaC:

Bronze: short retention (ingestion artifacts)

Silver: medium retention (validated datasets)

Gold: long retention (analytics & BI consumption)
---

## Modes of Operation
| Mode                 | Purpose                   | Characteristics                                          |
| -------------------- | ------------------------- | -------------------------------------------------------- |
| Local                | CI-safe dev/testing       | No cloud dependencies, deterministic                     |
| Azure (Dev)          | Cloud learning + showcase | Synapse serverless + ADLS + ADF                          |
| Azure (Prod Pattern) | Future expansion          | Private endpoints, governance, monitoring, orchestration |

-- CI pipelines run in local mode by default to avoid external dependencies and cloud charges.
---
## Tech Stack

- Python 3.11
- Pandas
- Pytest (data quality + transformation tests)
- Azure Data Factory
- Terraform (Azure)
- ADLS Gen2(hierarchical namespace)
- Synapse Serverless SQL
- ADF 
- GitHub Actions

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
