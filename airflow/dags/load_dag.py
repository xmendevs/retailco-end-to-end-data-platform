from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime, timedelta
import sys

# Ensure dlt pipeline modules are discoverable
sys.path.insert(0, "/opt/airflow/dlt_pipeline")
from load_pipeline import run_load_pipeline

default_args = {
    "owner": "retailco",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="retailco_pipeline",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule="@daily",
    catchup=False,
    tags=["retailco", "etl"],
) as dag:

    load_data = PythonOperator(
        task_id="load_lake_to_warehouse",
        python_callable=run_load_pipeline,
    )

    dbt_snapshot = BashOperator(
        task_id="dbt_snapshot",
        bash_command="cd /opt/airflow/dbt_project && dbt snapshot --profiles-dir /opt/airflow/dbt_project"
    )

    dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command="cd /opt/airflow/dbt_project && dbt run --profiles-dir /opt/airflow/dbt_project"
    )

    dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command="cd /opt/airflow/dbt_project && dbt test --profiles-dir /opt/airflow/dbt_project"
    )

    # Task Pipeline Dependencies
    load_data >> dbt_snapshot >> dbt_run >> dbt_test