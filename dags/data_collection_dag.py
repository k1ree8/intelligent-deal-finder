# dags/data_collection_dag.py
from datetime import datetime

from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator

with DAG(
    dag_id='process_avito_ads',
    description='DAG для сбора и обработки объявлений с Avito.',
    schedule_interval=None, # Пока отключим расписание, будем запускать вручную
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=['avito', 'data-collection'],
) as dag:
    run_worker_task = BashOperator(
        task_id='run_worker',
        bash_command='PYTHONPATH="/opt/airflow" python /opt/airflow/src/core/worker.py',
    )