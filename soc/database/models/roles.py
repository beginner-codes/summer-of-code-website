from sqlalchemy import Column, ForeignKey, Integer, Unicode
from soc.database.models.base import BaseModel


class Role(BaseModel):
    __tablename__ = "Roles"
    id = Column(Integer, primary_key=True)
    type = Column(Unicode(32), nullable=False)
    user_id = Column(Integer, ForeignKey("Users.id", ondelete="CASCADE"))
