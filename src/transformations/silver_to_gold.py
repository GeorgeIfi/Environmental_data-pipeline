import pandas as pd
from src.config.settings import SILVER_PATH, GOLD_PATH
from src.utils.azure_storage import AzureStorage
from src.utils.synapse_client import SynapseClient

def silver_to_gold():
    df = pd.read_parquet(f"{SILVER_PATH}/cleaned_data.parquet")
    agg_df = df.groupby(['date', 'location']).agg({'value': 'mean'}).reset_index()
    
    local_path = f"{GOLD_PATH}/aggregated_data.parquet"
    agg_df.to_parquet(local_path)
    
    # Upload to Azure Data Lake
    storage = AzureStorage()
    storage.upload_file(local_path, "gold/aggregated_data.parquet")
    
    # Create external table in Synapse for querying
    synapse = SynapseClient()
    synapse.create_external_table("gold_environmental_data", "gold/aggregated_data.parquet")