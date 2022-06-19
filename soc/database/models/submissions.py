from sqlalchemy import Column, ForeignKey, Integer, Unicode
from soc.database.models.base import BaseModel


class SubmissionModel(BaseModel):
    __tablename__ = "Submissions"
    id = Column(Integer, primary_key=True)
    type = Column(Unicode(32), nullable=False)
    link = Column(Unicode(512), nullable=False)
    description = Column(Unicode(4096), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.id"))
    challenge_id = Column(Integer, ForeignKey("Challenges.id", ondelete="CASCADE"))
