import pytest
from src.transformations.data_quality_checks import check_data_quality
import pandas as pd

def test_data_quality():
    df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    assert check_data_quality(df) == True