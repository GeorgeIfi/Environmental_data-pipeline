"""
Test documentation and running guide for Environmental Data Pipeline
"""

# Unit Tests for Environmental Data Pipeline (Pytest)

## Overview

Comprehensive test suite covering all transformation stages of the medallion architecture:
- **Bronze Layer**: CSV → Parquet ingestion
- **Silver Layer**: Data validation and cleaning
- **Gold Layer**: Aggregation and analytics preparation

**Test Statistics:**
-  **36 tests** passing
-  **100% pass rate**
- ⏱️ **2.12 seconds** total runtime

## Test Structure

### Test Files

```
tests/
├── conftest.py                      # Pytest fixtures and configuration
├── test_ingestion.py               # Bronze layer (CSV → Parquet) - 9 tests
├── test_bronze_to_silver.py        # Silver layer (Bronze → Silver) - 13 tests
├── test_silver_to_gold.py          # Gold layer (Silver → Gold) - 14 tests
└── __init__.py
```

## Fixtures (conftest.py)

Reusable test data and temporary directories:

### `tmp_data_dir`
Creates temporary directory structure mimicking medallion architecture:
```python
{
  "root": tmp_path,
  "landing": tmp_path / "landing",    # Incoming CSV files
  "bronze": tmp_path / "bronze",      # Parquet conversions
  "silver": tmp_path / "silver",      # Cleaned data
  "gold": tmp_path / "gold"           # Aggregations
}
```

### `sample_raw_csv`
6 rows of sample environmental data (PM2.5, NO2 pollutants):
```
date, location, latitude, longitude, pollutant_type, value, ...
2024-01-01, London, 51.5074, -0.1278, PM2.5, 35.5, ...
```

### `sample_bronze_parquet`
Bronze layer data with ingestion metadata:
```
[columns from CSV] + ingestion_timestamp + source_file
```

### `sample_silver_parquet`
Cleaned Silver layer data:
```
Parsed dates, no nulls, valid coordinates, positive values
```

### `bronze_with_invalid_data`
Bronze data with intentional errors for edge case testing:
- Invalid dates ("invalid-date")
- Invalid coordinates (lat=999, lon=500)
- Negative values (-5.1)
- Null values (None)

### `empty_parquet`
Empty Parquet file for error handling tests

## Test Coverage

### 1. Bronze Layer Ingestion (9 tests)

**File**: `test_ingestion.py`

Tests for CSV → Parquet transformation:

| Test | Purpose |
|------|---------|
| `test_ingest_csv_happy_path` | Successful CSV ingestion with metadata |
| `test_ingest_csv_parquet_format` | Output is valid Parquet format |
| `test_ingest_csv_source_file_metadata` | Source filename captured correctly |
| `test_ingest_csv_missing_file` | FileNotFoundError for missing input |
| `test_ingest_csv_empty_file` | ValueError for empty CSV |
| `test_ingest_csv_data_types_preserved` | Numeric/string types preserved |
| `test_ingest_csv_column_count` | All expected columns present |
| `test_ingest_csv_creates_output_directory` | Nested output dirs created |
| `test_ingest_csv_snappy_compression` | Snappy compression used |

**Key Assertions**:
- ✅ Output file exists
- ✅ Row count matches input
- ✅ Metadata columns added (ingestion_timestamp, source_file)
- ✅ Original columns preserved
- ✅ Correct data types (float, object)
- ✅ Snappy compression applied

---

### 2. Silver Layer Transformation (13 tests)

**File**: `test_bronze_to_silver.py`

Tests for Bronze → Silver data cleaning and validation:

| Test | Purpose |
|------|---------|
| `test_bronze_to_silver_happy_path` | Successful transformation |
| `test_bronze_to_silver_date_parsing` | Date column parsed to datetime |
| `test_bronze_to_silver_null_removal` | Nulls removed from critical columns |
| `test_bronze_to_silver_invalid_data_removal` | Invalid data filtered out |
| `test_bronze_to_silver_coordinate_validation` | Lat/lon within valid ranges |
| `test_bronze_to_silver_positive_values` | Negative values filtered |
| `test_bronze_to_silver_missing_input_file` | FileNotFoundError handling |
| `test_bronze_to_silver_empty_input` | ValueError for empty input |
| `test_bronze_to_silver_column_drop` | Original date column replaced |
| `test_bronze_to_silver_metadata_preserved` | Metadata columns retained |
| `test_bronze_to_silver_output_format` | Valid Parquet output |
| `test_bronze_to_silver_creates_output_directory` | Nested dirs created |
| `test_bronze_to_silver_data_integrity` | Valid data rows preserved |

**Key Assertions**:
- ✅ Date parsing to datetime64
- ✅ No nulls in critical columns (date, value, lat, lon)
- ✅ Latitude: -90 to 90
- ✅ Longitude: -180 to 180
- ✅ Values >= 0
- ✅ Metadata preserved (ingestion_timestamp, source_file)
- ✅ Row count correct after filtering

**Edge Cases Tested**:
- Invalid date strings → filtered
- Out-of-range coordinates → filtered
- Negative measurement values → filtered
- Null values → filtered

---

### 3. Gold Layer Transformation (14 tests)

**File**: `test_silver_to_gold.py`

Tests for Silver → Gold aggregation and analytics:

| Test | Purpose |
|------|---------|
| `test_silver_to_gold_happy_path` | Successful aggregation |
| `test_silver_to_gold_aggregation_columns` | avg_value, max_value, min_value, record_count |
| `test_silver_to_gold_grouping_columns` | date, location, pollutant_type, zone preserved |
| `test_silver_to_gold_aggregation_accuracy` | Mathematical correctness of aggregations |
| `test_silver_to_gold_sorting` | Results sorted by date, location, pollutant_type |
| `test_silver_to_gold_no_null_aggregations` | No nulls in aggregation results |
| `test_silver_to_gold_count_aggregation` | record_count is positive integer |
| `test_silver_to_gold_missing_input_file` | FileNotFoundError handling |
| `test_silver_to_gold_empty_input` | ValueError for empty input |
| `test_silver_to_gold_output_format` | Valid Parquet output |
| `test_silver_to_gold_creates_output_directory` | Nested dirs created |
| `test_silver_to_gold_min_max_relationship` | min <= avg <= max for each row |
| `test_silver_to_gold_multiple_locations` | Multi-location aggregation |
| `test_silver_to_gold_multiple_pollutants` | Multi-pollutant aggregation |

**Key Assertions**:
- ✅ Aggregation columns present (avg_value, max_value, min_value, record_count)
- ✅ Grouping columns preserved (date, location, pollutant_type, zone)
- ✅ Aggregations mathematically correct
- ✅ No nulls in results
- ✅ record_count > 0 and integer
- ✅ min_value <= avg_value <= max_value
- ✅ Sorted correctly

---

## Running the Tests

### Run All Tests
```bash
cd /workspaces/environmental-data-platform
python -m pytest tests/ -v
```

### Run Specific Test File
```bash
# Bronze layer only
python -m pytest tests/test_ingestion.py -v

# Silver layer only
python -m pytest tests/test_bronze_to_silver.py -v

# Gold layer only
python -m pytest tests/test_silver_to_gold.py -v
```

### Run Specific Test
```bash
python -m pytest tests/test_bronze_to_silver.py::TestBronzeToSilver::test_bronze_to_silver_happy_path -v
```

### Run with Coverage Report
```bash
pip install pytest-cov
python -m pytest tests/ --cov=src --cov-report=html
# Opens: htmlcov/index.html
```

### Run with Detailed Output
```bash
python -m pytest tests/ -vv --tb=long
```

### Run and Stop on First Failure
```bash
python -m pytest tests/ -x
```

---

## Test Execution Example

```
============================= test session starts ==============================
platform linux -- Python 3.12.1, pytest-9.0.2
collected 36 items

tests/test_bronze_to_silver.py::TestBronzeToSilver::test_bronze_to_silver_happy_path PASSED [  2%]
tests/test_bronze_to_silver.py::TestBronzeToSilver::test_bronze_to_silver_date_parsing PASSED [  5%]
...
tests/test_silver_to_gold.py::TestSilverToGold::test_silver_to_gold_multiple_pollutants PASSED [100%]

============================== 36 passed in 2.12s ==============================
```

---

## Data Quality Validation Strategy

### Bronze Layer (Ingestion)
- ✅ File existence check
- ✅ Empty dataset detection
- ✅ Column count verification
- ✅ Data type preservation
- ✅ Metadata addition (timestamp, source)

### Silver Layer (Cleaning)
- ✅ Null value removal
- ✅ Date parsing with error handling
- ✅ Coordinate range validation (-90 to 90 lat, -180 to 180 lon)
- ✅ Positive value enforcement
- ✅ Metadata preservation
- ✅ Row integrity checks

### Gold Layer (Aggregation)
- ✅ Grouping correctness (date, location, pollutant_type, zone)
- ✅ Aggregation accuracy (mean, min, max, count)
- ✅ Min-max relationship validation
- ✅ Record count accuracy
- ✅ Sorting consistency
- ✅ Multi-location/pollutant handling

---

## Error Handling

All transformation functions handle these errors:

1. **FileNotFoundError**: Missing input files
   - Test: `test_*_missing_input_file`

2. **ValueError**: Empty datasets
   - Test: `test_*_empty_input`

3. **Data Quality Issues**: Invalid data filtered gracefully
   - Test: `test_*_invalid_data_removal`

---

## CI/CD Integration

### GitHub Actions (Recommended)
```yaml
name: Test Transformations
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt pytest pyarrow
      - run: python -m pytest tests/ -v
```

### Local Pre-commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python -m pytest tests/ --tb=short
if [ $? -ne 0 ]; then
  echo "Tests failed, commit aborted"
  exit 1
fi
```

---

## Test Fixtures Best Practices

### Using Fixtures in Your Tests
```python
def test_example(sample_raw_csv, tmp_data_dir):
    """Test that uses fixtures"""
    input_path, df = sample_raw_csv
    output = tmp_data_dir["bronze"] / "output.parquet"
    
    # Your test here
    assert output.exists()
```

### Creating New Fixtures
```python
@pytest.fixture
def custom_data(tmp_path):
    """Create custom test data"""
    data = {...}
    df = pd.DataFrame(data)
    path = tmp_path / "data.parquet"
    df.to_parquet(path)
    return path, df
```

---

## Troubleshooting

### pytest: command not found
```bash
pip install pytest pyarrow
```

### ImportError: No module named 'src'
```bash
# Ensure you're in the project root
cd /workspaces/environmental-data-platform
python -m pytest tests/
```

### Tests timeout
```bash
# Add timeout option (seconds)
python -m pytest tests/ --timeout=10
```

### File permission denied
```bash
# Ensure tests can write to tmp_path
chmod 755 tests/
```

---

## Test Metrics

| Metric | Value |
|--------|-------|
| Total Tests | 36 |
| Pass Rate | 100% |
| Execution Time | ~2.12s |
| Code Coverage (target) | >90% |
| Transformation Functions Tested | 3 (ingest_csv, bronze_to_silver, silver_to_gold) |
| Edge Cases | 15+ |

---

## Future Test Enhancements

- [ ] Performance benchmarking tests
- [ ] Memory usage tests
- [ ] Azure Functions integration tests
- [ ] End-to-end pipeline tests
- [ ] Data Factory orchestration tests
- [ ] Schema validation tests
- [ ] Concurrent execution tests
- [ ] Rollback/recovery tests

---

## Author

Created for Environmental Data Engineering Pipeline
Covers all medallion architecture transformation stages
