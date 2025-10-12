from datetime import datetime, timedelta
from typing import Union


def parse_relative_date(relative_date_str: str) -> Union[datetime, None]:
    """
    Преобразует строку с относительной датой (напр., "5 минут назад")
    в объект datetime.
    """
    now = datetime.now()
    relative_date_str = relative_date_str.lower()

    try:
        if "только что" in relative_date_str:
            return now
        if "сегодня" in relative_date_str:
            time_str = relative_date_str.split(" в ")[1]
            hour, minute = map(int, time_str.split(":"))
            return now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if "вчера" in relative_date_str:
            yesterday = now - timedelta(days=1)
            time_str = relative_date_str.split(" в ")[1]
            hour, minute = map(int, time_str.split(":"))
            return yesterday.replace(hour=hour, minute=minute, second=0, microsecond=0)

        parts = relative_date_str.split()
        if len(parts) == 3 and "назад" in parts:
            value = int(parts[0])
            unit = parts[1]

            if "минут" in unit:
                return now - timedelta(minutes=value)
            if "час" in unit:
                return now - timedelta(hours=value)
            if "ден" in unit or "дня" in unit or "дней" in unit:
                return now - timedelta(days=value)

        return None
    except (ValueError, IndexError):
        return None
