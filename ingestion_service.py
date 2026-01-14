#!/usr/bin/env python3
"""
Automated Data Ingestion Service
Monitors landing folder and processes new files through the pipeline
"""
import os
import time
from pathlib import Path
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient
import subprocess

load_dotenv()

class DataIngestionService:
    def __init__(self):
        self.storage_account = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
        self.storage_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
        self.container = os.getenv("AZURE_CONTAINER", "environmental-data")
        
        self.blob_client = BlobServiceClient(
            account_url=f"https://{self.storage_account}.blob.core.windows.net",
            credential=self.storage_key
        )
        
    def check_landing_folder(self):
        """Check for new files in landing folder"""
        container_client = self.blob_client.get_container_client(self.container)
        
        # List all blobs in landing folder
        landing_blobs = container_client.list_blobs(name_starts_with="landing/")
        
        new_files = []
        for blob in landing_blobs:
            if blob.name.endswith('.csv'):
                new_files.append(blob.name)
        
        return new_files
    
    def download_and_process(self, blob_path):
        """Download file and run pipeline"""
        print(f"Processing: {blob_path}")
        
        # Download file
        local_path = f"temp_{Path(blob_path).name}"
        blob_client = self.blob_client.get_blob_client(
            container=self.container, 
            blob=blob_path
        )
        
        with open(local_path, "wb") as download_file:
            download_file.write(blob_client.download_blob().readall())
        
        # Run pipeline
        try:
            result = subprocess.run([
                "python", "run_pipeline.py", 
                "--raw-path", local_path
            ], capture_output=True, text=True, env={
                **os.environ,
                "JAVA_HOME": "/usr/lib/jvm/java-21-openjdk-amd64"
            })
            
            if result.returncode == 0:
                print("✓ Pipeline completed successfully")
                self.upload_results()
                self.move_processed_file(blob_path)
            else:
                print(f"✗ Pipeline failed: {result.stderr}")
                
        finally:
            # Cleanup
            if os.path.exists(local_path):
                os.remove(local_path)
    
    def upload_results(self):
        """Upload processed data to Azure"""
        layers = ["bronze", "silver", "gold"]
        files = ["raw_data.parquet", "silver_data.parquet", "gold_data.parquet"]
        
        for layer, file in zip(layers, files):
            local_dir = f"data/{layer}/{file}"
            if os.path.exists(local_dir):
                subprocess.run([
                    "az", "storage", "blob", "upload-batch",
                    "--account-name", self.storage_account,
                    "--destination", self.container,
                    "--source", local_dir,
                    "--destination-path", f"{layer}/weather/{file}",
                    "--overwrite"
                ])
    
    def move_processed_file(self, blob_path):
        """Move processed file from landing to raw folder"""
        # Copy to raw folder
        source_blob = self.blob_client.get_blob_client(
            container=self.container, blob=blob_path
        )
        
        # Create new path in raw folder
        filename = Path(blob_path).name
        raw_path = f"raw/{filename}"
        
        target_blob = self.blob_client.get_blob_client(
            container=self.container, blob=raw_path
        )
        
        # Copy blob
        target_blob.start_copy_from_url(source_blob.url)
        
        # Delete from landing
        source_blob.delete_blob()
        
        print(f"✓ Moved {blob_path} → {raw_path}")
    
    def run_continuous(self, interval=300):
        """Run continuous monitoring (default: 5 minutes)"""
        print(f"Starting continuous ingestion service...")
        print(f"Monitoring: {self.container}/landing/")
        print(f"Check interval: {interval} seconds")
        
        while True:
            try:
                new_files = self.check_landing_folder()
                
                if new_files:
                    print(f"Found {len(new_files)} new files")
                    for file_path in new_files:
                        self.download_and_process(file_path)
                else:
                    print("No new files found")
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                print("\\nStopping ingestion service...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    service = DataIngestionService()
    service.run_continuous()