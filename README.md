## Environmental Data Engineering Pipeline (Azure-centric)
## Overview

This project implements an end-to-end data engineering pipeline for ingesting, transforming, validating, and preparing environmental data for analytics and downstream consumption. It is designed using cloud-native data engineering principles, with Azure as the target platform, while remaining runnable locally for development and CI/CD.

The pipeline follows a layered medallion architecture (Raw → Bronze → Silver → Gold) and emphasizes infrastructure as code, data quality enforcement, and reproducible environments.

## Architecture
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
│  Bronze  │  Basic cleaning & standardization
└────┬─────┘
     ▼
┌──────────┐
│  Silver  │  Validated, enriched, analytics-ready
└────┬─────┘
     ▼
┌──────────┐
│   Gold   │  Curated outputs (KPIs / reporting)
└──────────┘

## Cloud mapping (Azure-oriented):

Raw / Bronze / Silver / Gold → Azure Data Lake Storage Gen2 containers

Orchestration → Apache Airflow

Infrastructure → Terraform

CI/CD → GitHub Actions

## Tech Stack

Python 3.11

Apache Airflow (orchestration)

Terraform (Azure infrastructure as code)

Azure Data Lake Storage Gen2

Pandas / Pytest (transformations & quality checks)

GitHub Actions (CI pipeline)

## Repository Structure
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
│       └── azure_storage.py
│
├── data/
│   ├── raw/        # ignored (runtime only)
│   ├── bronze/     # ignored
│   ├── silver/     # ignored
│   └── gold/       # ignored
│
├── tests/
│   └── test_quality.py
│
├── run_pipeline.py
├── requirements.txt
├── .gitignore
└── README.md

## Data Quality & Validation

Data quality is treated as a first-class concern, not an afterthought.

Implemented checks include:

Null / completeness checks

Schema validation

Basic value sanity checks (ranges, formats)

Quality checks are:

Executed during transformation stages

Enforced in CI using pytest

Designed to fail fast to prevent bad data propagation downstream

## Infrastructure as Code (Terraform)

All cloud resources are defined declaratively using Terraform, including:

Azure storage resources

Supporting data platform components

Key principles:

No state or secrets committed to Git

Environment-specific values handled via variables

Reproducible deployments

## Configuration & Secrets Management

Secrets are never hard-coded

Local development uses environment variables (.env, ignored)

CI/CD injects secrets securely

.env.example documents required variables without exposing values

## CI/CD

The CI pipeline performs:

Dependency installation

Static validation

Data quality tests

Failure on schema or completeness issues

This ensures:

Code quality

Data reliability

Safe iteration

## Design Principles Demonstrated

Separation of concerns

Cloud-first thinking

Immutable raw data

Config-driven execution

Defensive data engineering

Security-aware development

## Author

George Ifi
Data Engineer | Environmental Management MSc
Focused on cloud-native data platforms and environmental tech.