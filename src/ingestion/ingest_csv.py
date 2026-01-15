#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
from datetime import datetime


def ingest_csv(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Ingest raw CSV data into Bronze layer using Pandas
    
    Args:
        input_path: Path to input CSV file
        output_path: Path to output parquet file
        
    Returns:
        DataFrame with ingested data
    """
    print(f"Ingesting CSV from {input_path} to {output_path}")
    
    # Check if file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")
    
    # Define column names and types
    dtypes = {
        "date": str,
        "location": str,
        "latitude": float,
        "longitude": float,
        "site_type": str,
        "zone": str,
        "pollutant_type": str,
        "value": float,
        "unit": str,
        "status": str
    }
    
    # Read CSV with pandas
    df = pd.read_csv(str(input_path), dtype=dtypes)
    
    # Check if empty
    if df.empty:
        raise ValueError(f"Input CSV is empty: {input_path}")
    
    # Add ingestion metadata
    df['ingestion_timestamp'] = datetime.now()
    df['source_file'] = input_path.name
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Bronze layer as Parquet
    df.to_parquet(str(output_path), index=False, compression='snappy')
    
    print(f"✓ Ingested {len(df)} rows to Bronze layer")
    return df
