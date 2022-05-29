from sqlalchemy import Boolean, Column, DateTime, Integer, Unicode
from sqlalchemy.sql import func
from soc.database.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), nullable=False)
    avatar = Column(Unicode(256), nullable=True)
    email = Column(Unicode(256), nullable=False)
    joined = Column(DateTime, server_default=func.now())
    banned = Column(Boolean, default=False)
