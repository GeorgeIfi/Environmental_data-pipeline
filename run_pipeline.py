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
    parser = argparse.ArgumentParser(description="Run the weather environmental data pipeline.")
    parser.add_argument(
        "--raw-path",
        dest="raw_path",
        default=os.getenv("RAW_DATA_PATH"),
        help="Path to the raw CSV input file. Can also be set via RAW_DATA_PATH env var.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if not args.raw_path:
        print(
            "ERROR: No raw CSV path provided.\n"
            "Provide one via --raw-path or set RAW_DATA_PATH.\n"
            "Example: python run_pipeline.py --raw-path data/raw/your_file.csv",
            file=sys.stderr,
        )
        sys.exit(2)

    raw_path = Path(args.raw_path)

    if not raw_path.exists() or not raw_path.is_file():
        print(f"ERROR: Raw CSV path does not exist or is not a file: {raw_path}", file=sys.stderr)
        sys.exit(2)

    # Run pipeline stages
    ingest_csv(str(raw_path))
    bronze_to_silver()
    silver_to_gold()
    print("Pipeline completed successfully")


if __name__ == "__main__":
    main()
