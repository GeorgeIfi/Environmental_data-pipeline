# src/ingestion/ingest_csv.py

from pathlib import Path
import pandas as pd

BRONZE_PATH = Path("data/bronze")

def ingest_csv(input_path: str, output_path: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    # Decide output location
    out = Path(output_path) if output_path else BRONZE_PATH / "raw_data.parquet"

    # Ensure directory exists (fixes your CI error)
    out.parent.mkdir(parents=True, exist_ok=True)

    df.to_parquet(out, index=False)
    return df
