import pytest
from src.ingestion.ingest_csv import ingest_csv

def test_ingest_csv():
    df = ingest_csv("data/raw/8997590721.csv")
    assert len(df) > 0