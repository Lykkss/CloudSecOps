from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class ScanResult(Base):
    __tablename__ = "scan_result"

    id_scan        = Column(Integer, primary_key=True, index=True)
    scanned_at     = Column(DateTime(timezone=True), server_default=func.now())
    image_name     = Column(String(255), nullable=False)
    image_tag      = Column(String(100), nullable=False)
    git_sha        = Column(String(40))
    critical_count = Column(Integer, default=0)
    high_count     = Column(Integer, default=0)
    medium_count   = Column(Integer, default=0)
    low_count      = Column(Integer, default=0)
    # "passed" | "failed"
    status         = Column(String(20), nullable=False, default="passed")
    # JSON brut Trivy (Results[])
    raw_json       = Column(Text)
    triggered_by   = Column(String(100), default="ci")
