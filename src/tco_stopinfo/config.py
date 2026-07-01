from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class HttpConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8084
    workers: int = 1
    log_level: str = "info"


class MqttConfig(BaseModel):
    broker: str = "localhost"
    port: int = 1883
    tls: bool = False
    username: str | None = None
    password: str | None = None
    client_id: str = "tco-stopinfo-api"
    topic_prefix: str = "pis"
    reconnect_seconds: int = 5


class CacheConfig(BaseModel):
    fast_response_seconds: int = 10
    vehicle_ttl_seconds: int = 7200
    http_cache_max_age: int = 30


class AccountConfig(BaseModel):
    base_language: str = "fi"
    max_following_stops: int = 5
    max_connections_per_stop: int = 3
    fs_connection_mode: str = "compact"


class AppConfig(BaseModel):
    http: HttpConfig = Field(default_factory=HttpConfig)
    mqtt: MqttConfig = Field(default_factory=MqttConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    accounts: dict[str, AccountConfig] = Field(default_factory=lambda: {"hsl": AccountConfig()})

    def account(self, account: str) -> AccountConfig:
        return self.accounts.get(account.lower(), AccountConfig())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="TCO_", env_nested_delimiter="__")

    config_file: str | None = None


def load_config(path: str | Path | None = None) -> AppConfig:
    settings = Settings()
    config_path = Path(path or settings.config_file or "config.yaml")
    if config_path.is_file():
        with config_path.open(encoding="utf-8") as handle:
            raw: dict[str, Any] = yaml.safe_load(handle) or {}
        accounts = {
            name: AccountConfig(**values)
            for name, values in (raw.get("accounts") or {}).items()
        }
        return AppConfig(
            http=HttpConfig(**(raw.get("http") or {})),
            mqtt=MqttConfig(**(raw.get("mqtt") or {})),
            cache=CacheConfig(**(raw.get("cache") or {})),
            accounts=accounts or {"hsl": AccountConfig()},
        )
    return AppConfig()
