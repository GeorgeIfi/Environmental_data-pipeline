from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

from src.utils.azure_storage import AzureStorage


def _default_bronze_file() -> Path:
    bronze_dir = Path(os.getenv("BRONZE_DIR", "data/bronze"))
    return bronze_dir / os.getenv("BRONZE_FILE", "raw_data.parquet")


def _default_silver_file() -> Path:
    silver_dir = Path(os.getenv("SILVER_DIR", "data/silver"))
    return silver_dir / os.getenv("SILVER_FILE", "cleaned_data.parquet")


def bronze_to_silver(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    upload: bool = True,
    remote_path: str | None = None,
) -> str:
    """
    Reads a bronze parquet file, applies basic cleaning, writes a silver parquet file,
    optionally uploads to ADLS Gen2.

    Args:
        input_path: bronze parquet input path. If None, resolved from env defaults.
        output_path: silver parquet output path. If None, resolved from env defaults.
        upload: whether to upload the resulting file to ADLS Gen2.
        remote_path: remote path/key to upload to. If None, defaults to env SILVER_REMOTE_PATH
                     or "silver/<output filename>".

    Returns:
        str: local path to the silver parquet file
    """
    bronze_file = Path(input_path) if input_path is not None else _default_bronze_file()
    if not bronze_file.exists():
        raise FileNotFoundError(
            f"Bronze input not found: {bronze_file}. Ensure ingestion created it."
        )

    df = pd.read_parquet(bronze_file)

    if "date" not in df.columns:
        raise ValueError(
            f"Expected column 'date' not found in {bronze_file}. "
            f"Available columns: {list(df.columns)}"
        )

    # Normalize date column
    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    # Fail fast if date parsing produced nulls
    if df["date"].isna().any():
        bad_rows = int(df["date"].isna().sum())
        raise ValueError(
            f"Date parsing produced {bad_rows} null(s). "
            "Check the 'date' column format in the bronze dataset."
        )

    silver_file = Path(output_path) if output_path is not None else _default_silver_file()
    silver_file.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(silver_file, index=False)

    if upload:
        storage = AzureStorage()

        # Choose a sensible default remote key
        if remote_path is None:
            remote_path = os.getenv("SILVER_REMOTE_PATH")
        if remote_path is None:
            remote_path = f"silver/{silver_file.name}"

        storage.upload_file(str(silver_file), remote_path)

    return str(silver_file)
