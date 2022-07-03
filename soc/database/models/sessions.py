from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    BigInteger,
    Integer,
    Unicode,
)
from sqlalchemy.sql import func

from soc.database.models.base import BaseModel


class SessionModel(BaseModel):
    __tablename__ = "Sessions"
    id = Column(BigInteger, primary_key=True)
    revoked = Column(Boolean, default=False)
    created = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))
    values = Column(Unicode(2**12), default="")
