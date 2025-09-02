import yaml
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn


def load_yaml_config() -> dict:
    """
    Загружает конфигурацию из YAML файла.
    Сначала ищет путь для Docker (Airflow), потом для локального запуска.
    """
    # Путь внутри Docker контейнера
    docker_config_path = Path("/opt/airflow/configs/config.yaml")
    # Путь для локального запуска
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
    A class for storing and validating application settings.
    Automatically reads environment variables from the .env file
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
        """
        Generates a URL for connecting to the database.
        Format: postgresql+psycopg2://user:password@host:port/dbname
        """
        return f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    def get_parser_url(self, use_sort: bool = False) -> str:
        """
        Собирает URL для парсера на основе данных из config.yaml.

        Args:
            use_sort: Использовать ли сортировку по дате.
        """
        yaml_config = load_yaml_config()
        base_url = yaml_config["avito"]["base_url"]
        city = yaml_config["avito"]["search"]["city"]
        query = yaml_config["avito"]["search"]["query"].replace(" ", "+")

        url = f"{base_url}/{city}?q={query}"
        if use_sort:
            sort_param = yaml_config["parser"]["sort_by_date"]
            url += sort_param

        return url


settings = Settings()
