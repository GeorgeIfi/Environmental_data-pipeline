#!/usr/bin/env python3
from src.ingestion.ingest_csv import ingest_csv
from src.transformations.bronze_to_silver import bronze_to_silver
from src.transformations.silver_to_gold import silver_to_gold

def main():
    ingest_csv("data/raw/8997590721.csv")
    bronze_to_silver()
    silver_to_gold()
    print("Pipeline completed successfully")

if __name__ == "__main__":
    main()