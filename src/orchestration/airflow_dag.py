from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def run_pipeline():
    from src.ingestion.ingest_csv import ingest_csv
    from src.transformations.bronze_to_silver import bronze_to_silver
    from src.transformations.silver_to_gold import silver_to_gold
    
    ingest_csv("data/raw/8997590721.csv")
    bronze_to_silver()
    silver_to_gold()

dag = DAG('environmental_pipeline', start_date=datetime(2025, 1, 1), schedule_interval='@daily')
PythonOperator(task_id='run_pipeline', python_callable=run_pipeline, dag=dag)