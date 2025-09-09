# src/core/config.py

from pathlib import Path

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

    # --- Настройки из .env файла ---
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
        """
        Просто читает и возвращает готовый URL из config.yaml.
        """
        yaml_config = load_yaml_config()
        if "avito" in yaml_config and "target_url" in yaml_config["avito"]:
            return yaml_config["avito"]["target_url"]
        else:
            log.error("Ключ 'target_url' не найден в configs/config.yaml!")
            raise KeyError("target_url not found in config file")


settings = Settings()
