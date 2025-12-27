import pandas as pd

def validate_dataframe(df: pd.DataFrame, required_cols: list[str]) -> None:
    if df.empty:
        raise ValueError("Data quality failed: DataFrame is empty")

    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Data quality failed: missing required columns: {missing}")

    null_counts = df[required_cols].isnull().sum()
    bad = null_counts[null_counts > 0]
    if not bad.empty:
        raise ValueError(f"Data quality failed: nulls found in required columns: {bad.to_dict()}")
