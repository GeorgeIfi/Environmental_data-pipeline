import azure.functions as func
import json
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from src.transformations.bronze_to_silver import bronze_to_silver


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function: Bronze to Silver Transformation
    Cleans and validates data from Bronze to Silver layer
    
    Request body:
    {
        "storage_account": "stenvpipelineXXXX",
        "storage_key": "key...",
        "container": "environmental-data",
        "bronze_file": "bronze/raw_data.parquet"
    }
    """
    try:
        req_body = req.get_json()
        
        storage_account = req_body.get('storage_account')
        storage_key = req_body.get('storage_key')
        container = req_body.get('container', 'environmental-data')
        bronze_file = req_body.get('bronze_file', 'bronze/raw_data.parquet')
        
        # Download bronze parquet from Azure Storage
        blob_service_client = BlobServiceClient(
            f"https://{storage_account}.blob.core.windows.net",
            credential=storage_key
        )
        blob_client = blob_service_client.get_blob_client(container=container, blob=bronze_file)
        
        temp_bronze = Path("/tmp/bronze_data.parquet")
        with open(temp_bronze, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())
        
        # Run transformation
        silver_output = Path("/tmp/silver_data.parquet")
        df = bronze_to_silver(temp_bronze, silver_output)
        
        # Upload silver parquet to Azure Storage
        silver_blob_path = f"silver/cleaned_data.parquet"
        silver_blob_client = blob_service_client.get_blob_client(
            container=container,
            blob=silver_blob_path
        )
        with open(silver_output, "rb") as f:
            silver_blob_client.upload_blob(f, overwrite=True)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "stage": "silver_transformation",
                "rows_cleaned": len(df),
                "output_path": f"https://{storage_account}.blob.core.windows.net/{container}/{silver_blob_path}"
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "stage": "silver_transformation",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
