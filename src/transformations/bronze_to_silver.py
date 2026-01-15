#!/usr/bin/env python3
import pandas as pd
from pathlib import Path


def bronze_to_silver(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Transform Bronze → Silver using Pandas
    Clean and validate data with quality checks
    
    Args:
        input_path: Path to input parquet (Bronze)
        output_path: Path to output parquet (Silver)
        
    Returns:
        Cleaned DataFrame
    """
    print(f"Transforming Bronze to Silver: {input_path} → {output_path}")
    
    # Check if input exists
    if not input_path.exists():
        raise FileNotFoundError(f"Bronze input not found: {input_path}")
    
    # Read Bronze parquet
    df = pd.read_parquet(str(input_path))
    
    # Data quality checks
    if df.empty:
        raise ValueError(f"Bronze dataset is empty: {input_path}")
    
    # Clean and validate datetime column
    df['date_parsed'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
    
    # Check for parsing failures
    null_dates = df['date_parsed'].isna().sum()
    if null_dates > 0:
        print(f"⚠️  Warning: Date parsing failed for {null_dates} rows - dropping them")
        df = df[df['date_parsed'].notna()]
    
    # Remove null values and filter valid measurements
    df_silver = df[
        (df['date_parsed'].notna()) &
        (df['value'].notna()) &
        (df['value'] >= 0) &
        (df['latitude'] >= -90) &
        (df['latitude'] <= 90) &
        (df['longitude'] >= -180) &
        (df['longitude'] <= 180)
    ].copy()
    
    # Drop original date column and rename parsed date
    df_silver = df_silver.drop(columns=['date'])
    df_silver = df_silver.rename(columns={'date_parsed': 'date'})
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Silver layer
    df_silver.to_parquet(str(output_path), index=False, compression='snappy')
    
    print(f"✓ Cleaned {len(df_silver)} rows to Silver layer")
    return df_silver
