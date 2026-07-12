import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    platform = Column(String(20), nullable=False, index=True)
    platform_user_id = Column(String(100), nullable=False, index=True)
    name = Column(String(255))
    email = Column(String(255))
    phone = Column(String(50))
    profile_data = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<Customer {self.platform}:{self.platform_user_id}>"
