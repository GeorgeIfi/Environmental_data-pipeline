import pandas as pd
from pathlib import Path

from src.config.settings import BRONZE_PATH, SILVER_PATH
from src.utils.azure_storage import AzureStorage


def bronze_to_silver() -> str:
    """
    Reads bronze/raw_data.parquet, applies basic cleaning, writes silver/cleaned_data.parquet,
    then uploads to ADLS Gen2.

    Returns:
        str: local path to the silver parquet file
    """
    bronze_file = Path(BRONZE_PATH) / "raw_data.parquet"
    if not bronze_file.exists():
        raise FileNotFoundError(
            f"Bronze input not found: {bronze_file}. "
            "Ensure ingestion created it before running bronze_to_silver()."
        )

    df = pd.read_parquet(bronze_file)

    if "date" not in df.columns:
        raise ValueError(
            f"Expected column 'date' not found in {bronze_file}. "
            f"Available columns: {list(df.columns)}"
        )

    # Normalize date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Optional: fail fast if date parsing produced nulls
    if df["date"].isna().any():
        bad_rows = int(df["date"].isna().sum())
        raise ValueError(
            f"Date parsing produced {bad_rows} null(s). "
            "Check the 'date' column format in the bronze dataset."
        )

    silver_dir = Path(SILVER_PATH)
    silver_dir.mkdir(parents=True, exist_ok=True)

    local_path = silver_dir / "cleaned_data.parquet"
    df.to_parquet(local_path, index=False)

    # Upload to Azure Data Lake (remote path inside the filesystem)
    storage = AzureStorage()
    storage.upload_file(str(local_path), "silver/cleaned_data.parquet")

    return str(local_path)
