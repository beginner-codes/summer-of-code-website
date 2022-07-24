from sqlalchemy import Column, DateTime, ForeignKey, Integer, Unicode
from sqlalchemy.sql import func

from soc.database.models.base import BaseModel


class VoteModel(BaseModel):
    __tablename__ = "Votes"
    id = Column(Integer, primary_key=True)
    emoji = Column(Unicode(128), nullable=False)
    created = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("Users.id"))
    submission = Column(Integer, ForeignKey("Submissions.id", ondelete="CASCADE"))
