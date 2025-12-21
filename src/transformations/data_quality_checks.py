import pandas as pd

def check_data_quality(df: pd.DataFrame) -> bool:
    return not df.isnull().any().any() and len(df) > 0