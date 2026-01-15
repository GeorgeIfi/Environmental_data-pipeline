#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.ingestion.ingest_csv import ingest_csv
from src.transformations.bronze_to_silver import bronze_to_silver
from src.transformations.silver_to_gold import silver_to_gold


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the weather environmental data pipeline (Pandas-based).")

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


def main():
    """Execute the medallion architecture ETL pipeline (Pandas-based)"""
    
    args = parse_args()
    
    # Validate inputs
    raw_path = Path(args.raw_path)
    if not raw_path.exists():
        print(f"❌ Error: Raw data file not found: {raw_path}")
        sys.exit(1)

    bronze_path = Path(args.bronze_dir) / args.bronze_file
    silver_path = Path(args.silver_dir) / args.silver_file
    gold_path = Path(args.gold_dir) / args.gold_file

    try:
        # Stage 1: Ingestion (CSV → Bronze Parquet)
        print("\n" + "="*60)
        print("STAGE 1: DATA INGESTION (CSV → Bronze Parquet)")
        print("="*60)
        df_bronze = ingest_csv(raw_path, bronze_path)

        # Stage 2: Cleaning & Validation (Bronze → Silver Parquet)
        print("\n" + "="*60)
        print("STAGE 2: DATA CLEANING & VALIDATION (Bronze → Silver)")
        print("="*60)
        df_silver = bronze_to_silver(bronze_path, silver_path)

        # Stage 3: Aggregation & Analytics (Silver → Gold Parquet)
        print("\n" + "="*60)
        print("STAGE 3: AGGREGATION & ANALYTICS (Silver → Gold)")
        print("="*60)
        df_gold = silver_to_gold(silver_path, gold_path)

        print("\n" + "="*60)
        print("✅ Pipeline completed successfully!")
        print("="*60)
        print(f"📊 Data Summary:")
        print(f"  • Bronze: {len(df_bronze)} rows")
        print(f"  • Silver: {len(df_silver)} rows")
        print(f"  • Gold: {len(df_gold)} aggregations")

    except Exception as e:
        print(f"\n❌ Pipeline failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
