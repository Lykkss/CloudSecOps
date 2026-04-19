from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from core.database import Base


class LogEntry(Base):
    __tablename__ = "log_entry"

    id_log = Column(Integer, primary_key=True, index=True)
    id_user = Column(Integer, ForeignKey("user_account.id_user"), nullable=True)
    action = Column(String(255), nullable=False)
    ip_address = Column(String(45), nullable=True)   # IPv4 + IPv6
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="logs")
