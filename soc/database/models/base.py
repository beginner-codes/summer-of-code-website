from sqlalchemy.future import select
from sqlalchemy.orm import as_declarative as _as_declarative
from sqlalchemy.sql.expression import Select


@_as_declarative()
class BaseModel:
    @classmethod
    def select(cls, *conditions, **filters) -> Select:
        query: Select = select(cls)
        if conditions:
            query.where(*conditions)

        if filters:
            query.filter_by(**filters)

        return query

    __mapper_args__ = {"eager_defaults": True}
