from sqlalchemy.future import select
from sqlalchemy.orm import as_declarative as _as_declarative


@_as_declarative()
class BaseModel:
    @classmethod
    def select(cls) -> select:
        return select(cls)

    __mapper_args__ = {"eager_defaults": True}
