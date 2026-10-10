from typing import Literal

from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, PositiveInt, HttpUrl, field_validator
from sqlalchemy import URL

LogLevel = Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    debug: bool = True
    log_level: LogLevel = "INFO"
    log_json: bool = False
    delivery_cost_update_interval_min: int = 5

    @field_validator("log_level", mode="before")
    @classmethod
    def _upper(cls, value: str) -> str:
        return value.upper()


class PostgresSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="POSTGRES_",
        extra="ignore",
    )

    user: str
    password: SecretStr
    port: PositiveInt
    host: str
    db: str

    @property
    def database_url(self) -> URL:
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.user,
            password=self.password.get_secret_value(),
            host=self.host,
            port=self.port,
            database=self.db,
        )


class SessionSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="SESSION_COOKIE_", extra="ignore")

    name: str = "session_id"
    max_age: int = int(timedelta(days=30).total_seconds())
    secure: bool = False
    httponly: bool = True
    samesite: Literal["lax", "strict", "none"] = "lax"


class RedisSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="REDIS_", extra="ignore")

    host: str
    port: int
    db: int

    @property
    def url(self) -> str:
        return f"redis://{self.host}:{self.port}/{self.db}"


class CurrencyExchangerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="EXCHANGER_", extra="ignore")

    source_url: HttpUrl
    refresh_hours: int = 1


class Settings(BaseSettings):
    app: AppSettings = AppSettings()
    postgres: PostgresSettings = PostgresSettings()
    session: SessionSettings = SessionSettings()
    redis: RedisSettings = RedisSettings()
    exchanger: CurrencyExchangerSettings = CurrencyExchangerSettings()


settings = Settings()
