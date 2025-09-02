# src/core/sender.py
import sys
import requests
from src.core.config import settings
from src.core.logger import log

def send_telegram_message(message: str) -> None:
    """
    Отправляет сообщение в Telegram.
    
    Args:
        message: Текст сообщения для отправки.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    
    # URL API Telegram для отправки сообщений
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    
    # Параметры запроса
    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML", # Позволяет использовать HTML-теги для форматирования
    }
    
    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        log.info("Сообщение успешно отправлено в Telegram.")
    except requests.RequestException as e:
        log.error(f"Ошибка при отправке сообщения в Telegram: {e}")
        
# --- Блок для локального тестирования ---
if __name__ == "__main__":
    # Если скрипт запущен с аргументом (из Airflow), берем его
    if len(sys.argv) > 1:
        message_to_send = sys.argv[1]
        # Проверяем, что сообщение не пустое (если XCom был пуст)
        if message_to_send.strip():
             log.info("Получено сообщение из командной строки. Отправляем...")
             send_telegram_message(message_to_send)
        else:
             log.info("Получено пустое сообщение, отправка отменена.")

    # Иначе (если запущен локально без аргументов), используем тестовое
    else:
        log.info("Тестируем отправку сообщения в Telegram...")
        test_message = (
            "<b>🔥 Новое выгодное предложение! 🔥</b>\n\n"
            "<b>Название:</b> <a href='https://www.avito.ru'>Тестовая видеокарта RTX 9090</a>\n"
            "<b>Цена:</b> 100500 руб.\n\n"
        )
        send_telegram_message(test_message)