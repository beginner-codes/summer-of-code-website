from sqlalchemy import Column, Integer, Unicode, JSON

from soc.database.models.base import BaseModel


class SettingsModel(BaseModel):
    __tablename__ = "Settings"
    id = Column(Integer, primary_key=True)
    name = Column(Unicode(256), nullable=False)
    value = Column(JSON, nullable=False)
