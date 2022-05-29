from sqlalchemy import Column, DateTime, ForeignKey, Integer, Unicode
from sqlalchemy.sql import func
from soc.database.models.base import BaseModel


class Challenge(BaseModel):
    __tablename__ = "Challenges"
    id = Column(Integer, primary_key=True)
    title = Column(Unicode(512), nullable=False)
    description = Column(Unicode, nullable=False)
    created = Column(DateTime, server_default=func.now())
    start = Column(DateTime, nullable=False)
    end = Column(DateTime, nullable=False)
    user_id = Column(Integer, ForeignKey("Users.id"))
