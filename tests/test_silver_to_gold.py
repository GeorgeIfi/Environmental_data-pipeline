"""
Unit tests for Gold layer transformation (Silver → Gold)
Tests the silver_to_gold function from src/transformations/silver_to_gold.py
"""
import pytest
import pandas as pd
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.transformations.silver_to_gold import silver_to_gold


class TestSilverToGold:
    """Test suite for Silver to Gold transformation"""
    
    def test_silver_to_gold_happy_path(self, sample_silver_parquet, tmp_data_dir):
        """Test successful Silver → Gold transformation"""
        input_path, original_df = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "transformed.parquet"
        
        # Execute transformation
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify output exists
        assert output_path.exists(), "Gold parquet file was not created"
        
        # Verify result is DataFrame
        assert isinstance(result_df, pd.DataFrame)
        
        # Verify output has rows (aggregated, should be fewer than input)
        assert len(result_df) > 0, "Gold output is empty"
        assert len(result_df) <= len(original_df), "Gold should have aggregated fewer rows"
    
    def test_silver_to_gold_aggregation_columns(self, sample_silver_parquet, tmp_data_dir):
        """Test that aggregation columns are correctly created"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "agg_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify aggregation columns exist
        expected_agg_cols = ["avg_value", "max_value", "min_value", "record_count"]
        for col in expected_agg_cols:
            assert col in result_df.columns, f"Missing aggregation column: {col}"
    
    def test_silver_to_gold_grouping_columns(self, sample_silver_parquet, tmp_data_dir):
        """Test that grouping columns are preserved"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "group_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify grouping columns exist
        expected_group_cols = ["date", "location", "pollutant_type", "zone"]
        for col in expected_group_cols:
            assert col in result_df.columns, f"Missing grouping column: {col}"
    
    def test_silver_to_gold_aggregation_accuracy(self, sample_silver_parquet, tmp_data_dir):
        """Test that aggregations are mathematically correct"""
        input_path, original_df = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "accuracy_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify aggregations are correct by checking a specific group
        # Find a row with only one record for exact comparison
        for _, orig_row in original_df.iterrows():
            test_group = original_df[
                (original_df["date"] == orig_row["date"]) &
                (original_df["location"] == orig_row["location"]) &
                (original_df["pollutant_type"] == orig_row["pollutant_type"]) &
                (original_df["zone"] == orig_row["zone"])
            ]
            
            if len(test_group) == 1:  # Single record group for exact comparison
                expected_avg = test_group["value"].mean()
                expected_max = test_group["value"].max()
                expected_min = test_group["value"].min()
                expected_count = test_group["value"].count()
                
                # Find matching row in gold
                gold_match = result_df[
                    (result_df["date"] == orig_row["date"]) &
                    (result_df["location"] == orig_row["location"]) &
                    (result_df["pollutant_type"] == orig_row["pollutant_type"]) &
                    (result_df["zone"] == orig_row["zone"])
                ]
                
                if len(gold_match) > 0:
                    assert abs(gold_match.iloc[0]["avg_value"] - expected_avg) < 0.01
                    assert gold_match.iloc[0]["max_value"] == expected_max
                    assert gold_match.iloc[0]["min_value"] == expected_min
                    assert gold_match.iloc[0]["record_count"] == expected_count
                break
    
    def test_silver_to_gold_sorting(self, sample_silver_parquet, tmp_data_dir):
        """Test that output is sorted by date, location, and pollutant_type"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "sort_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify sorting
        sorted_df = result_df.sort_values(["date", "location", "pollutant_type"]).reset_index(drop=True)
        pd.testing.assert_frame_equal(result_df.reset_index(drop=True), sorted_df)
    
    def test_silver_to_gold_no_null_aggregations(self, sample_silver_parquet, tmp_data_dir):
        """Test that aggregation results don't have nulls"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "null_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify no nulls in aggregation columns
        assert result_df["avg_value"].notna().all()
        assert result_df["max_value"].notna().all()
        assert result_df["min_value"].notna().all()
        assert result_df["record_count"].notna().all()
    
    def test_silver_to_gold_count_aggregation(self, sample_silver_parquet, tmp_data_dir):
        """Test that record_count is positive integer"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "count_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # record_count should be positive integers
        assert (result_df["record_count"] > 0).all()
        assert (result_df["record_count"] == result_df["record_count"].astype(int)).all()
    
    def test_silver_to_gold_missing_input_file(self, tmp_data_dir):
        """Test error handling for missing input file"""
        missing_path = tmp_data_dir["silver"] / "nonexistent.parquet"
        output_path = tmp_data_dir["gold"] / "output.parquet"
        
        with pytest.raises(FileNotFoundError):
            silver_to_gold(missing_path, output_path)
    
    def test_silver_to_gold_empty_input(self, empty_parquet, tmp_data_dir):
        """Test error handling for empty input"""
        output_path = tmp_data_dir["gold"] / "output.parquet"
        
        with pytest.raises(ValueError):
            silver_to_gold(empty_parquet, output_path)
    
    def test_silver_to_gold_output_format(self, sample_silver_parquet, tmp_data_dir):
        """Test that output is valid Parquet with Snappy compression"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "format_test.parquet"
        
        silver_to_gold(input_path, output_path)
        
        # Verify it can be read as parquet
        df_read = pd.read_parquet(str(output_path))
        assert isinstance(df_read, pd.DataFrame)
    
    def test_silver_to_gold_creates_output_directory(self, sample_silver_parquet, tmp_data_dir):
        """Test that output directory is created if needed"""
        input_path, _ = sample_silver_parquet
        nested_output = tmp_data_dir["root"] / "nested" / "gold" / "output.parquet"
        
        # Ensure nested directory doesn't exist
        assert not nested_output.parent.exists()
        
        silver_to_gold(input_path, nested_output)
        
        # Verify nested directory was created
        assert nested_output.exists()
    
    def test_silver_to_gold_min_max_relationship(self, sample_silver_parquet, tmp_data_dir):
        """Test that min <= avg <= max for each aggregation"""
        input_path, _ = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "relationship_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # For each row, verify: min <= avg <= max
        for idx, row in result_df.iterrows():
            assert row["min_value"] <= row["avg_value"], f"Row {idx}: min > avg"
            assert row["avg_value"] <= row["max_value"], f"Row {idx}: avg > max"
            assert row["min_value"] <= row["max_value"], f"Row {idx}: min > max"
    
    def test_silver_to_gold_multiple_locations(self, sample_silver_parquet, tmp_data_dir):
        """Test aggregation across multiple locations"""
        input_path, original_df = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "locations_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify multiple locations are aggregated
        original_locations = original_df["location"].unique()
        result_locations = result_df["location"].unique()
        
        assert len(result_locations) > 0
        assert all(loc in original_locations for loc in result_locations)
    
    def test_silver_to_gold_multiple_pollutants(self, sample_silver_parquet, tmp_data_dir):
        """Test aggregation across multiple pollutant types"""
        input_path, original_df = sample_silver_parquet
        output_path = tmp_data_dir["gold"] / "pollutants_test.parquet"
        
        result_df = silver_to_gold(input_path, output_path)
        
        # Verify multiple pollutant types are aggregated
        original_pollutants = original_df["pollutant_type"].unique()
        result_pollutants = result_df["pollutant_type"].unique()
        
        assert len(result_pollutants) > 0
        assert all(p in original_pollutants for p in result_pollutants)
