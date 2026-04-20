from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from core.database import Base


class EbiosProject(Base):
    __tablename__ = "ebios_project"

    id_project  = Column(Integer, primary_key=True, index=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())
    name        = Column(String(255), nullable=False)
    scope       = Column(Text)           # Périmètre
    context     = Column(Text)           # Contexte organisationnel
    # "in_progress" | "completed"
    status      = Column(String(20), default="in_progress")
    id_author   = Column(Integer, ForeignKey("user_account.id_user"))


class EbiosAsset(Base):
    """Valeurs métier / Biens essentiels — Atelier 1."""
    __tablename__ = "ebios_asset"

    id_asset    = Column(Integer, primary_key=True, index=True)
    id_project  = Column(Integer, ForeignKey("ebios_project.id_project"), nullable=False)
    name        = Column(String(255), nullable=False)
    # "process" | "information" | "system"
    type        = Column(String(50))
    description = Column(Text)
    # 1=faible … 4=critique
    critical_level = Column(Integer, default=2)


class EbiosFearEvent(Base):
    """Événements redoutés — Atelier 1."""
    __tablename__ = "ebios_fear_event"

    id_event    = Column(Integer, primary_key=True, index=True)
    id_project  = Column(Integer, ForeignKey("ebios_project.id_project"), nullable=False)
    id_asset    = Column(Integer, ForeignKey("ebios_asset.id_asset"), nullable=True)
    impact      = Column(String(100))    # confidentialité / intégrité / disponibilité
    description = Column(Text)
    # 1=négligeable … 4=critique
    gravity     = Column(Integer, default=2)


class EbiosRiskSource(Base):
    """Sources de risque — Atelier 2."""
    __tablename__ = "ebios_risk_source"

    id_source   = Column(Integer, primary_key=True, index=True)
    id_project  = Column(Integer, ForeignKey("ebios_project.id_project"), nullable=False)
    name        = Column(String(255), nullable=False)
    # "state" | "criminal" | "terrorist" | "competitor" | "insider" | "activist"
    category    = Column(String(50))
    motivation  = Column(Text)
    resources   = Column(String(100))   # "faibles" | "moyennes" | "importantes"
    # 1=faible … 4=très pertinente
    pertinence  = Column(Integer, default=2)


class EbiosScenario(Base):
    """Scénarios stratégiques + opérationnels — Ateliers 3 & 4."""
    __tablename__ = "ebios_scenario"

    id_scenario      = Column(Integer, primary_key=True, index=True)
    id_project       = Column(Integer, ForeignKey("ebios_project.id_project"), nullable=False)
    id_risk_source   = Column(Integer, ForeignKey("ebios_risk_source.id_source"), nullable=True)
    id_fear_event    = Column(Integer, ForeignKey("ebios_fear_event.id_event"), nullable=True)
    # "strategic" | "operational"
    type             = Column(String(20), default="strategic")
    title            = Column(String(255), nullable=False)
    description      = Column(Text)
    # JSON : [{step, technique, mitreId}]
    attack_path      = Column(Text)
    # 1=faible … 4=très élevé
    likelihood       = Column(Integer, default=2)
    gravity          = Column(Integer, default=2)
    # likelihood × gravity
    risk_level       = Column(Integer, default=4)
    # "reduce" | "transfer" | "avoid" | "accept"
    treatment        = Column(String(20), default="reduce")
    measures         = Column(Text)     # JSON : mesures de sécurité
