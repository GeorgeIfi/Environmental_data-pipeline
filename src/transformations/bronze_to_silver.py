import pandas as pd
from src.config.settings import BRONZE_PATH, SILVER_PATH
from src.utils.azure_storage import AzureStorage

def bronze_to_silver():
    df = pd.read_parquet(f"{BRONZE_PATH}/raw_data.parquet")
    df['date'] = pd.to_datetime(df['date'])
    
    local_path = f"{SILVER_PATH}/cleaned_data.parquet"
    df.to_parquet(local_path)
    
    # Upload to Azure Data Lake
    storage = AzureStorage()
    storage.upload_file(local_path, "silver/cleaned_data.parquet")