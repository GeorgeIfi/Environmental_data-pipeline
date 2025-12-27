from __future__ import annotations

import os
from pathlib import Path
import pandas as pd


def _default_bronze_dir() -> Path:
    """
    Resolve bronze directory from environment.
    Falls back to 'data/bronze' for local dev only.
    """
    return Path(os.getenv("BRONZE_DIR", "data/bronze"))


def ingest_csv(input_path: str | Path, output_path: str | Path | None = None) -> pd.DataFrame:
    input_path = Path(input_path)

    # Negative case 1: Missing CSV
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")

    # Read
    df = pd.read_csv(input_path)

    # Negative case 2: Empty file / no rows
    if df.empty:
        raise ValueError(f"Input CSV is empty: {input_path}")

    # Decide output location (parameterised)
    if output_path is None:
        out = _default_bronze_dir() / "raw_data.parquet"
    else:
        out = Path(output_path)

    # Ensure directory exists (CI-safe)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Write
    df.to_parquet(out, index=False)
    return df
