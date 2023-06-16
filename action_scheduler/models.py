from typing import Any, Literal

from pydantic import BaseModel
from sqlalchemy.orm import Mapped, mapped_column
from typing_extensions import Self

from .database import Base


class ActionORM(Base):
    __tablename__ = 'action'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(unique=False, doc='Имя экшена.')
    command: Mapped[str] = mapped_column(doc='Команда экшена.')
    cron: Mapped[dict[str, Any]] = mapped_column(doc='Расписание.')
    merge_missed: Mapped[bool | None] = mapped_column(
        doc=(
            'True - для замены пропущенных экшенов одним, None - взять значение из'
            ' дефолтных настроек'
        )
    )
    actuality_time: Mapped[int | None] = mapped_column(
        doc=(
            'Время актуальности пропущенного экшена в сек (отрицательное значение -'
            ' бесконечность), None - взять из дефолтных настроек'
        )
    )

    @classmethod
    def from_pydantic(cls, pydantic_obj: 'ActionCreate') -> Self:
        return ActionORM(**pydantic_obj.dict(exclude={'id'}))

    def to_pydantic(self):
        return Action.parse_obj(self.to_dict())


class Cron(BaseModel):
    format: Literal['unix', 'apscheduler']
    params: dict


class ActionBase(BaseModel):
    name: str
    command: str
    cron: Cron
    merge_missed: bool | None = None
    actuality_time: int | None = None


class ActionCreate(ActionBase):
    pass


class Action(ActionBase):
    id: int
