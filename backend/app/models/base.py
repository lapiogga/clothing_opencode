from datetime import datetime
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.orm import declared_attr


class TimestampMixin:
    @declared_attr
    def id(cls):
        return Column(Integer, primary_key=True, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
