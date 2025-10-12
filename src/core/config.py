from pathlib import Path
from typing import Optional

import yaml
from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.core.logger import log


def load_yaml_config() -> dict:
    """
    Загружает конфигурацию из YAML файла.
    Сначала ищет путь для Docker (Airflow), потом для локального запуска.
    """
    docker_config_path = Path("/opt/airflow/configs/config.yaml")
    local_config_path = Path("configs/config.yaml")

    if docker_config_path.is_file():
        config_path = docker_config_path
    elif local_config_path.is_file():
        config_path = local_config_path
    else:
        raise FileNotFoundError(
            f"Config file not found. Looked in: {docker_config_path} and {local_config_path}"
        )

    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class Settings(BaseSettings):
    """
    Класс для хранения и валидации настроек приложения.
    Автоматически читает переменные окружения из файла .env
    и предоставляет методы для доступа к конфигурации из YAML.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str

    @property
    def database_url(self) -> PostgresDsn:
        """Собирает URL для подключения к базе данных."""
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


    def get_parser_url(self) -> str:
        """Читает и возвращает target_url из config.yaml."""
        yaml_config = load_yaml_config()
        try:
            return yaml_config["avito"]["target_url"]
        except (KeyError, TypeError):
            log.error("Ключ 'avito.target_url' не найден в configs/config.yaml!")
            raise KeyError("target_url not found in config file")

    def get_pages_to_scan(self) -> int:
        """Читает и возвращает pages_to_scan из config.yaml."""
        yaml_config = load_yaml_config()
        try:
            return int(yaml_config["avito"]["pages_to_scan"])
        except (KeyError, TypeError, ValueError):
            log.warning("Ключ 'avito.pages_to_scan' не найден или некорректен. Используется значение по умолчанию: 1.")
            return 1

    def get_profit_threshold(self) -> int:
        """Читает и возвращает profit_threshold из config.yaml."""
        yaml_config = load_yaml_config()
        try:
            return int(yaml_config["model"]["profit_threshold"])
        except (KeyError, TypeError, ValueError):
            log.warning("Ключ 'model.profit_threshold' не найден или некорректен. Используется значение по умолчанию: 5000.")
            return 5000

    def get_schedule_interval(self) -> Optional[str]:
        """Читает и возвращает schedule_interval из config.yaml."""
        yaml_config = load_yaml_config()
        try:
            return yaml_config["airflow"]["schedule_interval"]
        except (KeyError, TypeError):
            log.warning("Ключ 'airflow.schedule_interval' не найден. Используется значение по умолчанию: None (ручной запуск).")
            return None


settings = Settings()