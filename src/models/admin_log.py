"""
Admin activity log model for tracking administrative actions
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base


class AdminActivityLog(Base):
    __tablename__ = "admin_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)  # e.g., "user.update", "user.delete", "system.config"
    target_type = Column(String(50))  # e.g., "user", "league", "config"
    target_id = Column(Integer)  # ID of the affected entity
    details = Column(Text)  # JSON string with additional details
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    admin = relationship("User", foreign_keys=[admin_id])
    
    def __repr__(self):
        return f"<AdminActivityLog(id={self.id}, admin_id={self.admin_id}, action='{self.action}')>"