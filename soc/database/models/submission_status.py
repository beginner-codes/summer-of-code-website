from sqlalchemy import Column, DateTime, ForeignKey, Integer, Unicode
from sqlalchemy.sql import func
from soc.database.models.base import BaseModel


class SubmissionStatus(BaseModel):
    __tablename__ = "SubmissionStatus"
    id = Column(Integer, primary_key=True)
    status = Column(Unicode(32), nullable=False)
    updated = Column(DateTime, server_default=func.now())
    user_id = Column(Integer, ForeignKey("Users.id"))
    submission_id = Column(Integer, ForeignKey("Submissions.id", ondelete="CASCADE"))
