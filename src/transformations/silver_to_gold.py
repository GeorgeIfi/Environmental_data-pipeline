#!/usr/bin/env python3
from pathlib import Path
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, avg, max, min, count, date_format


def silver_to_gold(spark: SparkSession, input_path: Path, output_path: Path) -> DataFrame:
    """
    Transform Silver → Gold using PySpark
    Create analytical aggregations and metrics
    """
    print(f"Transforming Silver to Gold: {input_path} → {output_path}")
    
    # Check if input exists
    if not input_path.exists():
        raise FileNotFoundError(f"Silver input not found: {input_path}")
    
    # Read Silver parquet
    df = spark.read.parquet(str(input_path))
    
    # Data quality check
    if df.count() == 0:
        raise ValueError(f"Silver dataset is empty: {input_path}")
    
    # Create daily aggregations by location and pollutant type
    df_gold = df \
        .groupBy("date", "location", "pollutant_type", "zone") \
        .agg(
            avg("value").alias("avg_value"),
            max("value").alias("max_value"),
            min("value").alias("min_value"),
            count("*").alias("record_count")
        ) \
        .orderBy("date", "location", "pollutant_type")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Gold layer
    df_gold.write \
        .mode("overwrite") \
        .parquet(str(output_path))
    
    print(f"✓ Created {df_gold.count()} daily aggregations in Gold layer")
    return df_gold