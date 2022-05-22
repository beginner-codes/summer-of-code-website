from sqlalchemy import Column, ForeignKey, Integer, Text
from soc.models import BaseModel


class Role(BaseModel):
    __tablename__ = "Roles"
    id = Column(Integer, primary_key=True)
    type = Column(Text(32), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))
