#!/usr/bin/env python3
"""
Manual Data Ingestion
Process a single file through the complete pipeline
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def process_file(csv_file):
    """Process a single CSV file through the pipeline"""
    
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} not found")
        return False
    
    print(f"Processing: {csv_file}")
    
    # Run pipeline
    try:
        result = subprocess.run([
            "python", "run_pipeline.py", 
            "--raw-path", csv_file
        ], env={
            **os.environ,
            "JAVA_HOME": "/usr/lib/jvm/java-21-openjdk-amd64"
        })
        
        if result.returncode == 0:
            print("✓ Pipeline completed successfully")
            
            # Upload results to Azure
            upload_to_azure()
            return True
        else:
            print("✗ Pipeline failed")
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False

def upload_to_azure():
    """Upload processed data to Azure Storage"""
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
    container = "environmental-data"
    
    layers = [
        ("bronze", "raw_data.parquet"),
        ("silver", "silver_data.parquet"), 
        ("gold", "gold_data.parquet")
    ]
    
    for layer, filename in layers:
        local_dir = f"data/{layer}/{filename}"
        if os.path.exists(local_dir):
            print(f"Uploading {layer} layer...")
            subprocess.run([
                "az", "storage", "blob", "upload-batch",
                "--account-name", storage_account,
                "--destination", container,
                "--source", local_dir,
                "--destination-path", f"{layer}/weather/{filename}",
                "--overwrite"
            ])

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python process_single_file.py <csv_file>")
        print("Example: python process_single_file.py data/raw/new_data.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    success = process_file(csv_file)
    
    if success:
        print("\\n🎉 File processed successfully!")
        print("Data available in Azure Storage:")
        print("- Bronze: environmental-data/bronze/weather/")
        print("- Silver: environmental-data/silver/weather/") 
        print("- Gold: environmental-data/gold/weather/")
    else:
        print("\\n❌ Processing failed")
        sys.exit(1)