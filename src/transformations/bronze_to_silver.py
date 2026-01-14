#!/usr/bin/env python3
from pathlib import Path
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, to_timestamp, when, isnan, isnull


def bronze_to_silver(spark: SparkSession, input_path: Path, output_path: Path) -> DataFrame:
    """
    Transform Bronze → Silver using PySpark
    Clean and validate data with quality checks
    """
    print(f"Transforming Bronze to Silver: {input_path} → {output_path}")
    
    # Check if input exists
    if not input_path.exists():
        raise FileNotFoundError(f"Bronze input not found: {input_path}")
    
    # Read Bronze parquet
    df = spark.read.parquet(str(input_path))
    
    # Data quality checks
    if df.count() == 0:
        raise ValueError(f"Bronze dataset is empty: {input_path}")
    
    # Clean and validate datetime column
    df_cleaned = df.withColumn(
        "date_parsed", 
        to_timestamp(col("date"), "yyyy-MM-dd")
    )
    
    # Check for parsing failures
    null_dates = df_cleaned.filter(col("date_parsed").isNull()).count()
    if null_dates > 0:
        raise ValueError(f"Date parsing failed for {null_dates} rows")
    
    # Remove null values and filter valid measurements
    df_silver = df_cleaned \
        .filter(col("date_parsed").isNotNull()) \
        .filter(col("value").isNotNull()) \
        .filter(col("value") >= 0) \
        .filter(col("latitude").between(-90, 90)) \
        .filter(col("longitude").between(-180, 180)) \
        .drop("date") \
        .withColumnRenamed("date_parsed", "date")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Silver layer
    df_silver.write \
        .mode("overwrite") \
        .parquet(str(output_path))
    
    print(f"✓ Cleaned {df_silver.count()} rows to Silver layer")
    return df_silver