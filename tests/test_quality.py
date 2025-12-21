import pytest
import pandas as pd

def test_data_completeness():
    df = pd.DataFrame({'date': ['2025-01-01'], 'value': [10]})
    assert not df.isnull().any().any()