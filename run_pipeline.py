#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from pyspark.sql import SparkSession

load_dotenv()

from src.ingestion.ingest_csv import ingest_csv
from src.transformations.bronze_to_silver import bronze_to_silver
from src.transformations.silver_to_gold import silver_to_gold


def get_spark_session():
    """Create Spark session with Azure configuration"""
    return SparkSession.builder \
        .appName("EnvironmentalDataPipeline") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .getOrCreate()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the weather environmental data pipeline.")

    parser.add_argument(
        "--raw-path",
        dest="raw_path",
        default=os.getenv("RAW_DATA_PATH"),
        help="Path to the raw CSV input file (or set RAW_DATA_PATH).",
    )

    parser.add_argument(
        "--bronze-dir",
        dest="bronze_dir",
        default=os.getenv("BRONZE_DIR", "data/bronze"),
        help="Bronze output directory (or set BRONZE_DIR).",
    )
    parser.add_argument(
        "--silver-dir",
        dest="silver_dir",
        default=os.getenv("SILVER_DIR", "data/silver"),
        help="Silver output directory (or set SILVER_DIR).",
    )
    parser.add_argument(
        "--gold-dir",
        dest="gold_dir",
        default=os.getenv("GOLD_DIR", "data/gold"),
        help="Gold output directory (or set GOLD_DIR).",
    )

    parser.add_argument(
        "--bronze-file",
        dest="bronze_file",
        default=os.getenv("BRONZE_FILE", "raw_data.parquet"),
        help="Bronze file name (or set BRONZE_FILE).",
    )
    parser.add_argument(
        "--silver-file",
        dest="silver_file",
        default=os.getenv("SILVER_FILE", "silver_data.parquet"),
        help="Silver file name (or set SILVER_FILE).",
    )
    parser.add_argument(
        "--gold-file",
        dest="gold_file",
        default=os.getenv("GOLD_FILE", "gold_data.parquet"),
        help="Gold file name (or set GOLD_FILE).",
    )

    return parser.parse_args()


def _die(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def main() -> None:
    args = parse_args()

    if not args.raw_path:
        _die(
            "No raw CSV path provided. Use --raw-path or set RAW_DATA_PATH.\n"
            "Example: python run_pipeline.py --raw-path data/raw/your_file.csv"
        )

    raw_path = Path(args.raw_path)
    if not raw_path.exists() or not raw_path.is_file():
        _die(f"Raw CSV path does not exist or is not a file: {raw_path}")

    bronze_dir = Path(args.bronze_dir)
    silver_dir = Path(args.silver_dir)
    gold_dir = Path(args.gold_dir)

    # Ensure directories exist (CI-safe)
    bronze_dir.mkdir(parents=True, exist_ok=True)
    silver_dir.mkdir(parents=True, exist_ok=True)
    gold_dir.mkdir(parents=True, exist_ok=True)

    bronze_path = bronze_dir / args.bronze_file
    silver_path = silver_dir / args.silver_file
    gold_path = gold_dir / args.gold_file

    # Create Spark session
    spark = get_spark_session()
    
    try:
        # Run pipeline stages (parameterised end-to-end)
        ingest_csv(spark, raw_path, output_path=bronze_path)
        bronze_to_silver(spark, input_path=bronze_path, output_path=silver_path)
        silver_to_gold(spark, input_path=silver_path, output_path=gold_path)
        
        print("Pipeline completed successfully")
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
