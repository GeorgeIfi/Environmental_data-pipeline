"""
Pytest configuration and fixtures for transformation tests
"""
import pytest
import pandas as pd
from pathlib import Path
import tempfile
from datetime import datetime, timedelta


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Create temporary directories for test data"""
    landing = tmp_path / "landing"
    bronze = tmp_path / "bronze"
    silver = tmp_path / "silver"
    gold = tmp_path / "gold"
    
    landing.mkdir()
    bronze.mkdir()
    silver.mkdir()
    gold.mkdir()
    
    return {
        "root": tmp_path,
        "landing": landing,
        "bronze": bronze,
        "silver": silver,
        "gold": gold,
    }


@pytest.fixture
def sample_raw_csv(tmp_data_dir):
    """Create sample raw CSV data for ingestion tests"""
    data = {
        "date": [
            "2024-01-01", "2024-01-01", "2024-01-02",
            "2024-01-02", "2024-01-03", "2024-01-03"
        ],
        "location": ["London", "London", "Manchester", "Manchester", "London", "Manchester"],
        "latitude": [51.5074, 51.5074, 53.4808, 53.4808, 51.5074, 53.4808],
        "longitude": [-0.1278, -0.1278, -2.2426, -2.2426, -0.1278, -2.2426],
        "site_type": ["urban", "urban", "urban", "urban", "urban", "urban"],
        "zone": ["south", "south", "north", "north", "south", "north"],
        "pollutant_type": ["PM2.5", "NO2", "PM2.5", "NO2", "PM2.5", "NO2"],
        "value": [35.5, 42.3, 38.2, 45.1, 36.8, 43.9],
        "unit": ["µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³"],
        "status": ["valid", "valid", "valid", "valid", "valid", "valid"],
    }
    
    df = pd.DataFrame(data)
    csv_path = tmp_data_dir["landing"] / "weather_raw.csv"
    df.to_csv(csv_path, index=False)
    
    return csv_path, df


@pytest.fixture
def sample_bronze_parquet(tmp_data_dir):
    """Create sample bronze layer data"""
    data = {
        "date": [
            "2024-01-01", "2024-01-01", "2024-01-02",
            "2024-01-02", "2024-01-03", "2024-01-03"
        ],
        "location": ["London", "London", "Manchester", "Manchester", "London", "Manchester"],
        "latitude": [51.5074, 51.5074, 53.4808, 53.4808, 51.5074, 53.4808],
        "longitude": [-0.1278, -0.1278, -2.2426, -2.2426, -0.1278, -2.2426],
        "site_type": ["urban", "urban", "urban", "urban", "urban", "urban"],
        "zone": ["south", "south", "north", "north", "south", "north"],
        "pollutant_type": ["PM2.5", "NO2", "PM2.5", "NO2", "PM2.5", "NO2"],
        "value": [35.5, 42.3, 38.2, 45.1, 36.8, 43.9],
        "unit": ["µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³"],
        "status": ["valid", "valid", "valid", "valid", "valid", "valid"],
        "ingestion_timestamp": [datetime.now()] * 6,
        "source_file": ["weather_raw.csv"] * 6,
    }
    
    df = pd.DataFrame(data)
    parquet_path = tmp_data_dir["bronze"] / "weather_bronze.parquet"
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    return parquet_path, df


@pytest.fixture
def sample_silver_parquet(tmp_data_dir):
    """Create sample silver layer data"""
    data = {
        "location": ["London", "London", "Manchester", "Manchester", "London"],
        "latitude": [51.5074, 51.5074, 53.4808, 53.4808, 51.5074],
        "longitude": [-0.1278, -0.1278, -2.2426, -2.2426, -0.1278],
        "site_type": ["urban", "urban", "urban", "urban", "urban"],
        "zone": ["south", "south", "north", "north", "south"],
        "pollutant_type": ["PM2.5", "NO2", "PM2.5", "NO2", "PM2.5"],
        "value": [35.5, 42.3, 38.2, 45.1, 36.8],
        "unit": ["µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³"],
        "status": ["valid", "valid", "valid", "valid", "valid"],
        "ingestion_timestamp": [datetime.now()] * 5,
        "source_file": ["weather_raw.csv"] * 5,
        "date": pd.to_datetime(["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03"]),
    }
    
    df = pd.DataFrame(data)
    parquet_path = tmp_data_dir["silver"] / "weather_silver.parquet"
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    return parquet_path, df


@pytest.fixture
def bronze_with_invalid_data(tmp_data_dir):
    """Create bronze data with invalid/null values for edge case testing"""
    data = {
        "date": [
            "2024-01-01", "2024-01-01", "invalid-date",
            "2024-01-02", "2024-01-03", "2024-01-03"
        ],
        "location": ["London", "London", "Manchester", "Manchester", "London", "Manchester"],
        "latitude": [51.5074, 51.5074, 999.0, 53.4808, 51.5074, 53.4808],  # 999 is invalid
        "longitude": [-0.1278, -0.1278, -2.2426, 500.0, -0.1278, -2.2426],  # 500 is invalid
        "site_type": ["urban", "urban", "urban", "urban", "urban", "urban"],
        "zone": ["south", "south", "north", "north", "south", "north"],
        "pollutant_type": ["PM2.5", "NO2", "PM2.5", "NO2", "PM2.5", "NO2"],
        "value": [35.5, 42.3, 38.2, -5.1, None, 43.9],  # -5.1 and None are invalid
        "unit": ["µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³", "µg/m³"],
        "status": ["valid", "valid", "valid", "valid", "valid", "valid"],
        "ingestion_timestamp": [datetime.now()] * 6,
        "source_file": ["weather_raw.csv"] * 6,
    }
    
    df = pd.DataFrame(data)
    parquet_path = tmp_data_dir["bronze"] / "weather_bronze_invalid.parquet"
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    return parquet_path, df


@pytest.fixture
def empty_parquet(tmp_data_dir):
    """Create an empty parquet file for error handling tests"""
    df = pd.DataFrame()
    parquet_path = tmp_data_dir["bronze"] / "empty.parquet"
    df.to_parquet(parquet_path, index=False, compression="snappy")
    
    return parquet_path
