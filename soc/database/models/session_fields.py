from sqlalchemy import Column, ForeignKey, Integer, Unicode
from soc.database.models.base import BaseModel


class SessionField(BaseModel):
    __tablename__ = "SessionFields"
    id = Column(Integer, primary_key=True)
    data = Column(Unicode(8192), default="")
    session_id = Column(Integer, ForeignKey("Sessions.id", ondelete="CASCADE"))
