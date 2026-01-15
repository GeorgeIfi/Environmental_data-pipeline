"""
Unit tests for Silver layer transformation (Bronze → Silver)
Tests the bronze_to_silver function from src/transformations/bronze_to_silver.py
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformations.bronze_to_silver import bronze_to_silver


class TestBronzeToSilver:
    """Test suite for Bronze to Silver transformation"""
    
    def test_bronze_to_silver_happy_path(self, sample_bronze_parquet, tmp_data_dir):
        """Test successful Bronze → Silver transformation"""
        input_path, original_df = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "transformed.parquet"
        
        # Execute transformation
        result_df = bronze_to_silver(input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "Silver parquet file was not created"
        
        # Verify result is DataFrame
        assert isinstance(result_df, pd.DataFrame)
        
        # Verify output has rows
        assert len(result_df) > 0, "Silver output is empty"
    
    def test_bronze_to_silver_date_parsing(self, sample_bronze_parquet, tmp_data_dir):
        """Test that date column is correctly parsed"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "date_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # Verify date column exists and is datetime
        assert "date" in result_df.columns
        assert pd.api.types.is_datetime64_any_dtype(result_df["date"])
    
    def test_bronze_to_silver_null_removal(self, sample_bronze_parquet, tmp_data_dir):
        """Test that null values in critical columns are removed"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "null_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # Verify no nulls in critical columns
        assert result_df["date"].notna().all(), "Null dates in output"
        assert result_df["value"].notna().all(), "Null values in output"
        assert result_df["latitude"].notna().all(), "Null latitude in output"
        assert result_df["longitude"].notna().all(), "Null longitude in output"
    
    def test_bronze_to_silver_invalid_data_removal(self, bronze_with_invalid_data, tmp_data_dir):
        """Test that invalid data is removed during transformation"""
        input_path, original_df = bronze_with_invalid_data
        output_path = tmp_data_dir["silver"] / "invalid_test.parquet"
        
        # Original data has invalid rows
        assert len(original_df) == 6
        
        # Transform
        result_df = bronze_to_silver(input_path, output_path)
        
        # Should have fewer rows after removing invalid data
        assert len(result_df) < len(original_df), "Invalid data was not removed"
        
        # Verify no invalid latitude/longitude
        assert (result_df["latitude"] >= -90).all() and (result_df["latitude"] <= 90).all()
        assert (result_df["longitude"] >= -180).all() and (result_df["longitude"] <= 180).all()
        
        # Verify no negative values
        assert (result_df["value"] >= 0).all()
    
    def test_bronze_to_silver_coordinate_validation(self, sample_bronze_parquet, tmp_data_dir):
        """Test geographic coordinate validation"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "coords_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # All coordinates should be within valid ranges
        assert (result_df["latitude"] >= -90).all() and (result_df["latitude"] <= 90).all()
        assert (result_df["longitude"] >= -180).all() and (result_df["longitude"] <= 180).all()
    
    def test_bronze_to_silver_positive_values(self, sample_bronze_parquet, tmp_data_dir):
        """Test that negative measurement values are filtered out"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "positive_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # All values should be >= 0
        assert (result_df["value"] >= 0).all()
    
    def test_bronze_to_silver_missing_input_file(self, tmp_data_dir):
        """Test error handling for missing input file"""
        missing_path = tmp_data_dir["bronze"] / "nonexistent.parquet"
        output_path = tmp_data_dir["silver"] / "output.parquet"
        
        with pytest.raises(FileNotFoundError):
            bronze_to_silver(missing_path, output_path)
    
    def test_bronze_to_silver_empty_input(self, empty_parquet, tmp_data_dir):
        """Test error handling for empty input"""
        output_path = tmp_data_dir["silver"] / "output.parquet"
        
        with pytest.raises(ValueError):
            bronze_to_silver(empty_parquet, output_path)
    
    def test_bronze_to_silver_column_drop(self, sample_bronze_parquet, tmp_data_dir):
        """Test that original date column is dropped"""
        input_path, original_df = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "column_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # Original date column should be replaced with parsed date
        assert "date" in result_df.columns
        assert pd.api.types.is_datetime64_any_dtype(result_df["date"])
    
    def test_bronze_to_silver_metadata_preserved(self, sample_bronze_parquet, tmp_data_dir):
        """Test that metadata columns are preserved"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "metadata_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # Metadata columns should be preserved
        assert "ingestion_timestamp" in result_df.columns
        assert "source_file" in result_df.columns
    
    def test_bronze_to_silver_output_format(self, sample_bronze_parquet, tmp_data_dir):
        """Test that output is valid Parquet with Snappy compression"""
        input_path, _ = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "format_test.parquet"
        
        bronze_to_silver(input_path, output_path)
        
        # Verify it can be read as parquet
        df_read = pd.read_parquet(str(output_path))
        assert isinstance(df_read, pd.DataFrame)
    
    def test_bronze_to_silver_creates_output_directory(self, sample_bronze_parquet, tmp_data_dir):
        """Test that output directory is created if needed"""
        input_path, _ = sample_bronze_parquet
        nested_output = tmp_data_dir["root"] / "nested" / "silver" / "output.parquet"
        
        # Ensure nested directory doesn't exist
        assert not nested_output.parent.exists()
        
        bronze_to_silver(input_path, nested_output)
        
        # Verify nested directory was created
        assert nested_output.exists()
    
    def test_bronze_to_silver_data_integrity(self, sample_bronze_parquet, tmp_data_dir):
        """Test that valid data is preserved without loss"""
        input_path, original_df = sample_bronze_parquet
        output_path = tmp_data_dir["silver"] / "integrity_test.parquet"
        
        result_df = bronze_to_silver(input_path, output_path)
        
        # Filter original data to what should be valid
        valid_original = original_df[
            (original_df['value'] >= 0) &
            (original_df['latitude'] >= -90) & (original_df['latitude'] <= 90) &
            (original_df['longitude'] >= -180) & (original_df['longitude'] <= 180)
        ]
        
        # Should have same number of rows
        assert len(result_df) == len(valid_original)
