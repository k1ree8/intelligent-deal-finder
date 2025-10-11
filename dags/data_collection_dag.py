# dags/data_collection_dag.py (исправленная версия)

import json
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.operators.bash import BashOperator
# <-- УДАЛИЛИ ИМПОРТ 'settings' ОТСЮДА -->


def get_schedule_from_config():
    """
    Вспомогательная функция, которая выполняется ВНУТРИ DAG,
    чтобы безопасно получить расписание.
    """
    import sys
    sys.path.insert(0, "/opt/airflow") # Временно добавляем src в путь
    from src.core.config import settings
    return settings.get_schedule_interval()


@dag(
    dag_id="process_avito_ads",
    description="DAG для сбора, обработки и уведомления о НОВЫХ ВЫГОДНЫХ объявлениях с Avito.",
    schedule_interval=get_schedule_from_config(), # <-- ТЕПЕРЬ ПОЛУЧАЕМ РАСПИСАНИЕ ТАК
    start_date=datetime(2023, 1, 1),
    catchup=False,
    tags=["avito", "data-collection", "ml"],
    default_args={
        'retries': 2,
        'retry_delay': timedelta(minutes=5),
    }
)
def process_avito_ads_dag():
    gather_data_task = BashOperator(
        task_id="gather_data_task",
        bash_command='PYTHONPATH="/opt/airflow" python /opt/airflow/src/core/worker.py',
        do_xcom_push=True,
    )

    @task
    def predict_and_filter_task(all_new_ads_json: str):
        """
        Загружает модель, предсказывает цены и фильтрует только выгодные объявления.
        """
        import sys
        sys.path.insert(0, "/opt/airflow") # <-- Этот импорт здесь уже был и он правильный
        from src.ml.predictor import predict_and_filter

        try:
            new_ads = json.loads(all_new_ads_json)
        except (json.JSONDecodeError, TypeError):
            new_ads = []

        if not new_ads:
            return json.dumps([])

        profitable_ads = predict_and_filter(new_ads)
        return json.dumps(profitable_ads, default=str)


    @task
    def send_notifications_task(profitable_ads_json: str):
        """
        Принимает JSON-строку с ВЫГОДНЫМИ объявлениями и отправляет уведомления.
        """
        import sys
        sys.path.insert(0, "/opt/airflow") # <-- Этот импорт здесь уже был и он правильный
        from src.core.sender import send_telegram_message

        try:
            profitable_ads = json.loads(profitable_ads_json)
        except (json.JSONDecodeError, TypeError):
            profitable_ads = []

        if not profitable_ads:
            print("Выгодных объявлений нет, уведомление не отправляем.")
            return

        print(f"Отправляем уведомления для {len(profitable_ads)} ВЫГОДНЫХ объявлений.")
        
        for ad in profitable_ads:
            profit = int(ad.get('profit', 0))
            predicted_price = int(ad.get('predicted_price', 0))
            
            message = (
                f"<b>🔥🔥🔥 Найдено выгодное предложение! 🔥🔥🔥</b>\n\n"
                f"<b>{ad.get('title', 'Без заголовка')}</b>\n\n"
                f"<b>Цена:</b> {ad.get('price', 'N/A')} руб.\n"
                f"<b>Ожидаемая цена:</b> {predicted_price} руб.\n"
                f"<b>💥 ВЫГОДА: ~{profit} руб. 💥</b>\n\n"
                f"<a href='{ad.get('url', '#')}'>🔗 Ссылка на объявление</a>"
            )
            send_telegram_message(message)

    all_ads = gather_data_task.output
    profitable_ads = predict_and_filter_task(all_ads)
    send_notifications_task(profitable_ads)


process_avito_ads_dag()