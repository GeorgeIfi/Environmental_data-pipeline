#!/usr/bin/env python3
"""
Package pipeline code for Azure Batch deployment
"""
import zipfile
import os
from pathlib import Path

def create_pipeline_package():
    """Create env_pipeline.zip with all necessary files"""
    
    # Files to include in the package
    files_to_package = [
        "requirements.txt",
        "run_pipeline.py", 
        "upload_to_adls.py",
        ".env",
        "src/ingestion/ingest_csv.py",
        "src/transformations/bronze_to_silver.py", 
        "src/transformations/silver_to_gold.py",
        "src/utils/azure_storage.py",
        "data/raw/weather_raw.csv"
    ]
    
    # Create artifacts directory if it doesn't exist
    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)
    
    zip_path = artifacts_dir / "env_pipeline.zip"
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_package:
            if os.path.exists(file_path):
                # Preserve directory structure in zip
                zipf.write(file_path, file_path)
                print(f"Added: {file_path}")
            else:
                print(f"Warning: {file_path} not found, skipping")
    
    print(f"\\nPackage created: {zip_path}")
    print(f"Package size: {zip_path.stat().st_size / 1024:.1f} KB")
    
    return zip_path

if __name__ == "__main__":
    create_pipeline_package()