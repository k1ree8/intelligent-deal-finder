import logging
import sys


def setup_logger():
    """Настраивает и возвращает кастомный логгер."""
    logger = logging.getLogger("IntelligentDealFinder")
    logger.setLevel(logging.INFO)

    if logger.hasHandlers():
        return logger

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s (%(filename)s:%(lineno)d)"
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    import os

    os.makedirs("logs", exist_ok=True)
    file_handler = logging.FileHandler("logs/app.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


log = setup_logger()
