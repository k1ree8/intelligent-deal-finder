from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import PostgresDsn

class Settings(BaseSettings):
    """
    A class for storing and validating application settings.
    Automatically reads environment variables from the .env file
    """
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra='ignore')

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

settings = Settings()