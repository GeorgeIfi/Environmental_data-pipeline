#!/usr/bin/env python3
from pathlib import Path
from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import col, current_timestamp, lit
from pyspark.sql.types import StructType, StructField, StringType, DoubleType


def ingest_csv(spark: SparkSession, input_path: Path, output_path: Path) -> DataFrame:
    """
    Ingest raw CSV data into Bronze layer using PySpark
    """
    print(f"Ingesting CSV from {input_path} to {output_path}")
    
    # Check if file exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_path}")
    
    # Define schema for better performance
    schema = StructType([
        StructField("date", StringType(), True),
        StructField("location", StringType(), True),
        StructField("latitude", DoubleType(), True),
        StructField("longitude", DoubleType(), True),
        StructField("site_type", StringType(), True),
        StructField("zone", StringType(), True),
        StructField("pollutant_type", StringType(), True),
        StructField("value", DoubleType(), True),
        StructField("unit", StringType(), True),
        StructField("status", StringType(), True)
    ])
    
    # Read CSV with schema
    df = spark.read \
        .option("header", "true") \
        .option("inferSchema", "false") \
        .schema(schema) \
        .csv(str(input_path))
    
    # Check if empty
    if df.count() == 0:
        raise ValueError(f"Input CSV is empty: {input_path}")
    
    # Add ingestion metadata
    df_with_metadata = df \
        .withColumn("ingestion_timestamp", current_timestamp()) \
        .withColumn("source_file", lit(str(input_path.name)))
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Bronze layer as Parquet
    df_with_metadata.write \
        .mode("overwrite") \
        .parquet(str(output_path))
    
    print(f"✓ Ingested {df_with_metadata.count()} rows to Bronze layer")
    return df_with_metadata