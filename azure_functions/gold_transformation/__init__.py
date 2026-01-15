import azure.functions as func
import json
from pathlib import Path
from azure.storage.blob import BlobServiceClient
from src.transformations.silver_to_gold import silver_to_gold


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function: Silver to Gold Transformation
    Aggregates and creates analytics dataset for Gold layer
    
    Request body:
    {
        "storage_account": "stenvpipelineXXXX",
        "storage_key": "key...",
        "container": "environmental-data",
        "silver_file": "silver/cleaned_data.parquet"
    }
    """
    try:
        req_body = req.get_json()
        
        storage_account = req_body.get('storage_account')
        storage_key = req_body.get('storage_key')
        container = req_body.get('container', 'environmental-data')
        silver_file = req_body.get('silver_file', 'silver/cleaned_data.parquet')
        
        # Download silver parquet from Azure Storage
        blob_service_client = BlobServiceClient(
            f"https://{storage_account}.blob.core.windows.net",
            credential=storage_key
        )
        blob_client = blob_service_client.get_blob_client(container=container, blob=silver_file)
        
        temp_silver = Path("/tmp/silver_data.parquet")
        with open(temp_silver, "wb") as f:
            download_stream = blob_client.download_blob()
            f.write(download_stream.readall())
        
        # Run transformation
        gold_output = Path("/tmp/gold_data.parquet")
        df = silver_to_gold(temp_silver, gold_output)
        
        # Upload gold parquet to Azure Storage
        gold_blob_path = f"gold/analytics_data.parquet"
        gold_blob_client = blob_service_client.get_blob_client(
            container=container,
            blob=gold_blob_path
        )
        with open(gold_output, "rb") as f:
            gold_blob_client.upload_blob(f, overwrite=True)
        
        return func.HttpResponse(
            json.dumps({
                "status": "success",
                "stage": "gold_aggregation",
                "rows_aggregated": len(df),
                "output_path": f"https://{storage_account}.blob.core.windows.net/{container}/{gold_blob_path}"
            }),
            status_code=200,
            mimetype="application/json"
        )
        
    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "stage": "gold_aggregation",
                "error": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )
