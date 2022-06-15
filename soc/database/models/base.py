from typing import Callable

from sqlalchemy.future import select
from sqlalchemy.orm import declarative_base as _declarative_base

BaseModel = _declarative_base()
BaseModel.select: Callable[[], select] = classmethod(lambda cls: select(cls))
