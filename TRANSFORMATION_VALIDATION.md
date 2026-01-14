# Data Transformation and Validation

## Overview

This document outlines the files responsible for data transformation and validation in the Environmental Data Pipeline.

## Transformation Files

### 1. `src/transformations/bronze_to_silver.py` - Primary Transformation
**Purpose:** Clean and validate raw data from Bronze to Silver layer

**Key Features:**
- **Data Quality Checks:** Validates input file existence and non-empty datasets
- **Datetime Parsing:** Converts string datetime to proper timestamp format with validation
- **Outlier Filtering:** 
  - Temperature: -50°C to 60°C
  - Humidity: 0% to 100%
  - Pressure: 800 to 1200 hPa
  - Wind Speed: >= 0
- **Null Value Removal:** Filters out records with missing critical data
- **Error Handling:** Fails fast with descriptive error messages

### 2. `src/transformations/silver_to_gold.py` - Analytical Transformation
**Purpose:** Create analytical aggregations from Silver to Gold layer

**Key Features:**
- **Daily Aggregations:** Groups data by date
- **Statistical Metrics:**
  - Average, maximum, minimum temperature
  - Average humidity, pressure, wind speed
  - Record count per day
- **Data Validation:** Checks for empty datasets
- **Sorted Output:** Orders results by date

## Data Validation Features

### Input Validation (`ingest_csv.py`)
- File existence verification
- Empty dataset detection
- Schema enforcement with predefined structure
- Metadata addition (ingestion timestamp, source file)

### Quality Assurance (`bronze_to_silver.py`)
- **Datetime Validation:** Ensures all datetime fields parse correctly
- **Range Validation:** Applies realistic bounds to sensor readings
- **Completeness Checks:** Removes incomplete records
- **Failure Reporting:** Provides detailed error messages for debugging

### Output Validation (`silver_to_gold.py`)
- Empty dataset prevention
- Required column validation
- Aggregation integrity checks

## Data Flow

```
Raw CSV → Bronze (Ingestion + Metadata)
    ↓
Bronze → Silver (Cleaning + Validation)
    ↓
Silver → Gold (Aggregation + Analytics)
```

## Error Handling Strategy

- **Fail Fast:** Pipeline stops immediately on critical errors
- **Descriptive Messages:** Clear error descriptions for troubleshooting
- **Data Quality Gates:** Each stage validates input before processing
- **Graceful Cleanup:** Spark session properly closed on completion or failure

## Primary Validation File

**`src/transformations/bronze_to_silver.py`** contains the most comprehensive data validation and transformation logic, serving as the primary data quality assurance component in the pipeline.