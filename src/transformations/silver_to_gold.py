from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

from src.utils.azure_storage import AzureStorage
from src.utils.synapse_client import SynapseClient


def _default_silver_file() -> Path:
    silver_dir = Path(os.getenv("SILVER_DIR", "data/silver"))
    return silver_dir / os.getenv("SILVER_FILE", "cleaned_data.parquet")


def _default_gold_file() -> Path:
    gold_dir = Path(os.getenv("GOLD_DIR", "data/gold"))
    return gold_dir / os.getenv("GOLD_FILE", "aggregated_data.parquet")


def silver_to_gold(
    input_path: str | Path | None = None,
    output_path: str | Path | None = None,
    *,
    upload: bool = True,
    remote_path: str | None = None,
    create_synapse_table: bool = True,
    table_name: str | None = None,
    external_location: str | None = None,
) -> str:
    """
    Reads a silver parquet file, aggregates to gold (mean value by date/location),
    writes a gold parquet file, optionally uploads to ADLS and optionally creates a Synapse external table.

    Args:
        input_path: silver parquet input path. If None, resolved from env defaults.
        output_path: gold parquet output path. If None, resolved from env defaults.
        upload: whether to upload the resulting file to ADLS Gen2.
        remote_path: remote path/key to upload to. If None, defaults to env GOLD_REMOTE_PATH
                     or "gold/<output filename>".
        create_synapse_table: whether to create/update an external table in Synapse.
        table_name: Synapse external table name (default from env SYNAPSE_TABLE_NAME or 'gold_environmental_data').
        external_location: The ADLS path/key Synapse should point to (defaults to remote_path).

    Returns:
        str: local path to the gold parquet file
    """
    silver_file = Path(input_path) if input_path is not None else _default_silver_file()
    if not silver_file.exists():
        raise FileNotFoundError(f"Silver input not found: {silver_file}")

    df = pd.read_parquet(silver_file)

    required_cols = {"date", "location", "value"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            f"Missing required columns {sorted(missing)} in {silver_file}. "
            f"Available columns: {list(df.columns)}"
        )

    agg_df = (
        df.groupby(["date", "location"], as_index=False)
          .agg(value=("value", "mean"))
    )

    gold_file = Path(output_path) if output_path is not None else _default_gold_file()
    gold_file.parent.mkdir(parents=True, exist_ok=True)
    agg_df.to_parquet(gold_file, index=False)

    resolved_remote_path = remote_path
    if resolved_remote_path is None:
        resolved_remote_path = os.getenv("GOLD_REMOTE_PATH")
    if resolved_remote_path is None:
        resolved_remote_path = f"gold/{gold_file.name}"

    if upload:
        storage = AzureStorage()
        storage.upload_file(str(gold_file), resolved_remote_path)

    # Synapse should generally reference the remote ADLS path/key
    if create_synapse_table:
        synapse = SynapseClient()
        if table_name is None:
            table_name = os.getenv("SYNAPSE_TABLE_NAME", "gold_environmental_data")
        if external_location is None:
            external_location = resolved_remote_path
        synapse.create_external_table(table_name, external_location)

    return str(gold_file)
