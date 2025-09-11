# dags/data_collection_dag.py
import json  # <-- Добавляем импорт
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator


@dag(
    dag_id="process_avito_ads",
    description="DAG для сбора, обработки и уведомления о новых объявлениях с Avito.",
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["avito", "data-collection"],
        default_args={
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    }
)
def process_avito_ads_dag():
    gather_data_task = BashOperator(
        task_id="gather_data_task",
        bash_command='PYTHONPATH="/opt/airflow" python /opt/airflow/src/core/worker.py --pages 59',
        do_xcom_push=True,
    )

    #    backfill_data_task = BashOperator(
    #        task_id='backfill_data_task',
    #        bash_command='PYTHONPATH="/opt/airflow" python /opt/airflow/src/core/worker.py --sort',
    #        do_xcom_push=True,
    #    )

    @task
    def send_notifications_task(ads_json_str: str):
        """
        Принимает JSON-строку с объявлениями, парсит ее и отправляет уведомления.
        """
        import sys

        sys.path.insert(0, "/opt/airflow")
        # Явно преобразуем JSON-строку в Python-объект
        try:
            new_ads = json.loads(ads_json_str)
        except (json.JSONDecodeError, TypeError):
            new_ads = []

        if not new_ads:
            print("Новых объявлений нет, уведомление не отправляем.")
            return

        print(f"Отправляем уведомления для {len(new_ads)} объявлений.")

        import sys

        sys.path.insert(0, "/opt/airflow/src")
        from src.core.sender import send_telegram_message

        for ad in new_ads:
            message = (
                f"<b>🔥 Новое объявление: {ad.get('title', 'Без заголовка')} 🔥</b>\n\n"
                f"<b>Цена:</b> {ad.get('price', 'Не указана')} руб.\n"
                f"<a href='{ad.get('url', '#')}'>🔗 Ссылка на объявление</a>"
            )
            send_telegram_message(message)

    gather_data_task

    # Вызываем вторую задачу, передавая ей результат первой
    # send_notifications_task(gather_data_task.output)


process_avito_ads_dag()
