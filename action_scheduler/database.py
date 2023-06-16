from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.types import JSON

from .config import config

engine = create_engine(
    config.actions_db.database_url, echo=config.test.echo_actions_db_engine
)


class Base(DeclarativeBase):
    type_annotation_map = {dict[str, Any]: JSON}

    def to_dict(self) -> dict[str, Any]:
        return {col.name: getattr(self, col.name) for col in self.__table__.columns}

    def __repr__(self) -> str:
        kwargs = ', '.join(
            f'{field}={value!r}' for field, value in self.to_dict().items()
        )
        return f'{type(self).__name__}({kwargs})'


def create_db_and_tables():
    Base.metadata.create_all(engine)
