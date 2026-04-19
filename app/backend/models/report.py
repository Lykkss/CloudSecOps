from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class ForensicReport(Base):
    __tablename__ = "forensic_report"

    id_report         = Column(Integer, primary_key=True, index=True)
    created_at        = Column(DateTime(timezone=True), server_default=func.now())
    updated_at        = Column(DateTime(timezone=True), onupdate=func.now())
    title             = Column(String(255), nullable=False)
    # "draft" | "final"
    status            = Column(String(20), nullable=False, default="draft")
    id_incident       = Column(Integer, ForeignKey("incident.id_incident"), nullable=True)
    executive_summary = Column(Text)
    # JSON : [{"id", "title", "severity", "description", "evidence"}]
    findings          = Column(Text)
    # JSON : [{"priority", "action", "owner"}]
    recommendations   = Column(Text)
    id_author         = Column(Integer, ForeignKey("user_account.id_user"), nullable=True)
