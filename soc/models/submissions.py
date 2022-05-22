from sqlalchemy import Column, ForeignKey, Integer, Text, Unicode
from soc.models import BaseModel


class Submission(BaseModel):
    __tablename__ = "Submissions"
    id = Column(Integer, primary_key=True)
    type = Column(Text(32), nullable=False)
    link = Column(Unicode(512), nullable=False)
    description = Column(Unicode(4096), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.id"))
    challenge_id = Column(Integer, ForeignKey("Challenges.id", ondelete="CASCADE"))
