import pandas as pd
import pytest
from src.ingestion.ingest_csv import ingest_csv


def test_ingest_csv_success(tmp_path):
    # Arrange: create a temporary CSV
    raw_csv = tmp_path / "input.csv"
    raw_csv.write_text("date,value\n2025-01-01,10\n")

    bronze_output = tmp_path / "bronze" / "raw_data.parquet"

    # Act
    df = ingest_csv(raw_csv, output_path=bronze_output)

    # Assert
    assert not df.empty
    assert bronze_output.exists()


def test_ingest_csv_missing_file(tmp_path):
    missing_csv = tmp_path / "missing.csv"

    with pytest.raises(FileNotFoundError):
        ingest_csv(missing_csv)


def test_ingest_csv_empty_file(tmp_path):
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("date,value\n")

    with pytest.raises(ValueError):
        ingest_csv(empty_csv)
