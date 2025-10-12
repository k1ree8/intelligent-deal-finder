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

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    params = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
    }

    try:
        response = requests.post(url, params=params)
        response.raise_for_status()
        log.info("Сообщение успешно отправлено в Telegram.")
    except requests.RequestException as e:
        log.error(f"Ошибка при отправке сообщения в Telegram: {e}")