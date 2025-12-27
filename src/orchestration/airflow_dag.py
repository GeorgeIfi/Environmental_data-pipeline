from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.models import Variable
from datetime import datetime


def run_pipeline(**context):
    from src.ingestion.ingest_csv import ingest_csv
    from src.transformations.bronze_to_silver import bronze_to_silver
    from src.transformations.silver_to_gold import silver_to_gold

    raw_path = Variable.get("RAW_DATA_PATH")

    ingest_csv(raw_path)
    bronze_to_silver()
    silver_to_gold()


with DAG(
    dag_id="environmental_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule_interval="@daily",
    catchup=False,
    tags=["environment", "data-pipeline"],
) as dag:

    run_pipeline_task = PythonOperator(
        task_id="run_pipeline",
        python_callable=run_pipeline,
    )
