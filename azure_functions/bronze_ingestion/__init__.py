import azure.functions as func
import json
import os
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from dotenv import load_dotenv
from src.ingestion.ingest_csv import ingest_csv


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function: Bronze Ingestion
    Ingests CSV data from Azure Storage to Bronze layer
    
    Request body:
    {
        "storage_account": "stenvpipelineXXXX",
        "storage_key": "key...",
        "container": "environmental-data",
        "csv_file": "landing/weather_data.csv"
    }
    """
    try:
        req_body = req.get_json()
        
        storage_account = req_body.get('storage_account')
        storage_key = req_body.get('storage_key')
        container = req_body.get('container', 'environmental-data')
        csv_file = req_body.get('csv_file', 'landing/weather_raw.csv')
        
        # Download CSV from Azure Storage to temp location
        blob_service_client = BlobServiceClient(
            f"https://{storage_account}.blob.core.windows.net",
            credential=storage_key
        )
        blob_client = blob_service_client.get_blob_client(container=container, blob=csv_file)
        
        temp_csv = Path("/tmp/input.csv")
        with open(temp_csv, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())
        
        # Run ingestion
        bronze_output = Path("/tmp/bronze_data.parquet")
        df = ingest_csv(temp_csv, bronze_output)
        
        # Upload bronze parquet to Azure Storage
        bronze_blob_path = f"bronze/raw_data.parquet"
        bronze_blob_client = blob_service_client.get_blob_client(
            container=container, 
            blob=bronze_blob_path
        )
        with open(bronze_output, "rb") as f:
            bronze_blob_client.upload_blob(f, overwrite=True)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "stage": "bronze_ingestion",
                "rows_ingested": len(df),
                "output_path": f"https://{storage_account}.blob.core.windows.net/{container}/{bronze_blob_path}"
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "stage": "bronze_ingestion",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
