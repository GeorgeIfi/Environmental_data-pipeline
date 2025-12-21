import pandas as pd
from src.config.settings import BRONZE_PATH

def ingest_csv(file_path: str) -> pd.DataFrame:
    df = pd.read_csv(file_path)
    df.to_parquet(f"{BRONZE_PATH}/raw_data.parquet")
    return df