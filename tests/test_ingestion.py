"""
Unit tests for Bronze layer ingestion (CSV → Parquet)
Tests the ingest_csv function from src/ingestion/ingest_csv.py
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.ingestion.ingest_csv import ingest_csv


class TestIngestCsv:
    """Test suite for CSV ingestion to Bronze layer"""
    
    def test_ingest_csv_happy_path(self, sample_raw_csv, tmp_data_dir):
        """Test successful CSV ingestion to Bronze parquet"""
        input_path, original_df = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "ingested.parquet"
        
        # Execute ingestion
        result_df = ingest_csv(input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "Bronze parquet file was not created"
        
        # Verify row count matches
        assert len(result_df) == len(original_df), "Row count mismatch after ingestion"
        
        # Verify metadata columns were added
        assert "ingestion_timestamp" in result_df.columns, "Missing ingestion_timestamp column"
        assert "source_file" in result_df.columns, "Missing source_file column"
        
        # Verify original columns preserved
        original_cols = set(original_df.columns)
        result_cols = set(result_df.columns) - {"ingestion_timestamp", "source_file"}
        assert original_cols == result_cols, "Original columns were modified"
    
    def test_ingest_csv_parquet_format(self, sample_raw_csv, tmp_data_dir):
        """Test that output is valid Parquet format"""
        input_path, _ = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "format_test.parquet"
        
        ingest_csv(input_path, output_path)
        
        # Verify it can be read as parquet
        df_read = pd.read_parquet(str(output_path))
        assert isinstance(df_read, pd.DataFrame), "Output is not a valid Parquet file"
        assert len(df_read) > 0, "Parquet file is empty"
    
    def test_ingest_csv_source_file_metadata(self, sample_raw_csv, tmp_data_dir):
        """Test that source filename is captured correctly"""
        input_path, _ = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "metadata_test.parquet"
        
        result_df = ingest_csv(input_path, output_path)
        
        # Verify source_file column
        assert result_df["source_file"].unique()[0] == input_path.name
    
    def test_ingest_csv_missing_file(self, tmp_data_dir):
        """Test error handling for non-existent input file"""
        missing_path = tmp_data_dir["landing"] / "nonexistent.csv"
        output_path = tmp_data_dir["bronze"] / "output.parquet"
        
        with pytest.raises(FileNotFoundError):
            ingest_csv(missing_path, output_path)
    
    def test_ingest_csv_empty_file(self, tmp_data_dir):
        """Test error handling for empty CSV"""
        empty_csv = tmp_data_dir["landing"] / "empty.csv"
        empty_csv.write_text("")
        output_path = tmp_data_dir["bronze"] / "empty_output.parquet"
        
        with pytest.raises((ValueError, pd.errors.EmptyDataError)):
            ingest_csv(empty_csv, output_path)
    
    def test_ingest_csv_data_types_preserved(self, sample_raw_csv, tmp_data_dir):
        """Test that data types are preserved correctly"""
        input_path, _ = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "dtype_test.parquet"
        
        result_df = ingest_csv(input_path, output_path)
        
        # Verify numeric columns are numeric
        assert pd.api.types.is_float_dtype(result_df["latitude"])
        assert pd.api.types.is_float_dtype(result_df["longitude"])
        assert pd.api.types.is_float_dtype(result_df["value"])
        
        # Verify string columns are string/object
        assert pd.api.types.is_object_dtype(result_df["location"])
        assert pd.api.types.is_object_dtype(result_df["zone"])
    
    def test_ingest_csv_column_count(self, sample_raw_csv, tmp_data_dir):
        """Test that all expected columns are present"""
        input_path, _ = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "columns_test.parquet"
        
        result_df = ingest_csv(input_path, output_path)
        
        expected_cols = [
            "date", "location", "latitude", "longitude", "site_type", "zone",
            "pollutant_type", "value", "unit", "status"
        ]
        
        for col in expected_cols:
            assert col in result_df.columns, f"Missing column: {col}"
    
    def test_ingest_csv_creates_output_directory(self, sample_raw_csv, tmp_data_dir):
        """Test that output directory is created if it doesn't exist"""
        input_path, _ = sample_raw_csv
        nested_output = tmp_data_dir["root"] / "nested" / "dirs" / "output.parquet"
        
        # Ensure nested directory doesn't exist
        assert not nested_output.parent.exists()
        
        ingest_csv(input_path, nested_output)
        
        # Verify nested directory was created
        assert nested_output.exists()
    
    def test_ingest_csv_snappy_compression(self, sample_raw_csv, tmp_data_dir):
        """Test that output uses Snappy compression"""
        input_path, _ = sample_raw_csv
        output_path = tmp_data_dir["bronze"] / "compression_test.parquet"
        
        ingest_csv(input_path, output_path)
        
        # Read with pyarrow to check compression
        import pyarrow.parquet as pq
        parquet_file = pq.ParquetFile(str(output_path))
        
        # Verify Snappy compression is used
        assert parquet_file.schema_arrow.metadata is not None
