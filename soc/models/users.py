from sqlalchemy import Boolean, Column, DateTime, Integer, Text, Unicode
from sqlalchemy.sql import func
from soc.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "Users"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(64), nullable=False)
    avatar = Column(Text(256), nullable=True)
    email = Column(Text(256), nullable=False)
    joined = Column(DateTime, server_default=func.now())
    banned = Column(Boolean, default=False)
