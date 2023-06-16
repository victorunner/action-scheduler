from typing import Any

from pydantic import BaseModel, BaseSettings, KafkaDsn, PositiveInt
from sqlalchemy import URL

from .utils import read_yaml_file_to_dict


class DatabaseConfig(BaseModel):
    dialect: str  # пример: postgresql
    driver: str | None = None  # пример: psycopg2
    username: str | None = None
    password: str | None = None
    host: str | None = None
    port: int | None = None
    database: str

    @property
    def database_url(self) -> URL:
        drivername = f'{self.dialect}+{self.driver}' if self.driver else self.dialect
        url = URL.create(
            drivername=drivername,
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )
        return url


class ActionDefaults(BaseModel):
    merge_missed: bool
    actuality_time: int


class ActionConfig(BaseModel):
    callback: str
    defaults: ActionDefaults


class TestConfig(BaseModel):
    write_sample_actions_to_db: bool = False
    print_apscheduler_jobs: bool = False
    echo_actions_db_engine: bool = False


class KafkaConfig(BaseModel):
    server: KafkaDsn
    topic: str


def yaml_config_settings_source(settings: BaseSettings) -> dict[str, Any]:
    encoding = settings.__config__.env_file_encoding
    return read_yaml_file_to_dict('config.yaml', encoding=encoding)


class Config(BaseSettings):
    debug: bool = False
    actions_db: DatabaseConfig
    track_changes_period: PositiveInt = 30  # sec
    internal_db: DatabaseConfig | None = None
    action: ActionConfig
    kafka: KafkaConfig | None = None
    test: TestConfig = TestConfig()

    class Config:
        env_nested_delimiter = '__'
        env_file = '.env'
        env_file_encoding = 'utf-8'

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                yaml_config_settings_source,
                file_secret_settings,
            )


config = Config()
