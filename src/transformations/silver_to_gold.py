#!/usr/bin/env python3
import pandas as pd
from pathlib import Path


def silver_to_gold(input_path: Path, output_path: Path) -> pd.DataFrame:
    """
    Transform Silver → Gold using Pandas
    Create analytical aggregations and metrics
    
    Args:
        input_path: Path to input parquet (Silver)
        output_path: Path to output parquet (Gold)
        
    Returns:
        Aggregated DataFrame
    """
    print(f"Transforming Silver to Gold: {input_path} → {output_path}")
    
    # Check if input exists
    if not input_path.exists():
        raise FileNotFoundError(f"Silver input not found: {input_path}")
    
    # Read Silver parquet
    df = pd.read_parquet(str(input_path))
    
    # Data quality check
    if df.empty:
        raise ValueError(f"Silver dataset is empty: {input_path}")
    
    # Create daily aggregations by location and pollutant type
    df_gold = df.groupby(['date', 'location', 'pollutant_type', 'zone']).agg(
        avg_value=('value', 'mean'),
        max_value=('value', 'max'),
        min_value=('value', 'min'),
        record_count=('value', 'count')
    ).reset_index()
    
    # Sort by date and location
    df_gold = df_gold.sort_values(['date', 'location', 'pollutant_type'])
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Gold layer
    df_gold.to_parquet(str(output_path), index=False, compression='snappy')
    
    print(f"✓ Created {len(df_gold)} daily aggregations in Gold layer")
    return df_gold
