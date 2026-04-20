from sqlalchemy import Column, DateTime, Integer, String, Text, func

from core.database import Base


class MobileScan(Base):
    __tablename__ = "mobile_scan"

    id_scan      = Column(Integer, primary_key=True, index=True)
    scanned_at   = Column(DateTime(timezone=True), server_default=func.now())
    app_name     = Column(String(255))
    package_name = Column(String(255))
    version      = Column(String(50))
    platform     = Column(String(20), default="android")   # android | ios
    file_name    = Column(String(255))
    mobsf_hash   = Column(String(64))                       # hash retourné par MobSF
    # Scores de sécurité MobSF (sur 100)
    security_score    = Column(Integer)
    # Compteurs par sévérité
    critical_count    = Column(Integer, default=0)
    high_count        = Column(Integer, default=0)
    warning_count     = Column(Integer, default=0)
    info_count        = Column(Integer, default=0)
    # "completed" | "failed" | "pending"
    status            = Column(String(20), default="pending")
    # JSON brut du rapport MobSF
    raw_json          = Column(Text)
    # Permissions dangereuses (JSON list)
    dangerous_perms   = Column(Text)
    # Trackers détectés (JSON list)
    trackers          = Column(Text)
