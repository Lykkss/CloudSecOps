from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class Incident(Base):
    __tablename__ = "incident"

    id_incident       = Column(Integer, primary_key=True, index=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())
    # "iam_compromise" | "data_breach" | "privilege_escalation" | …
    type              = Column(String(100), nullable=False)
    title             = Column(String(255), nullable=False)
    # "critical" | "high" | "medium" | "low"
    severity          = Column(String(20), nullable=False, default="high")
    # "open" | "investigating" | "resolved"
    status            = Column(String(20), nullable=False, default="open")
    affected_resource = Column(String(255))
    description       = Column(Text)
    # JSON : liste d'événements horodatés [{"ts":..., "event":...}]
    timeline          = Column(Text)
    # JSON : indicateurs de compromission (IOC)
    ioc               = Column(Text)
    id_user           = Column(Integer, ForeignKey("user_account.id_user"), nullable=True)
