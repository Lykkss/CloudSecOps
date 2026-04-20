-- ============================================================
-- INITIALISATION BASE DE DONNÉES — CloudSecOps
-- DDL + données initiales (rôles + admin par défaut)
-- ============================================================

-- Tables
CREATE TABLE IF NOT EXISTS role (
    id_role     SERIAL PRIMARY KEY,
    name        VARCHAR(50) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS permission (
    id_permis   SERIAL PRIMARY KEY,
    action      VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS role_permissions (
    id_role    INTEGER REFERENCES role(id_role),
    id_permis  INTEGER REFERENCES permission(id_permis),
    PRIMARY KEY (id_role, id_permis)
);

CREATE TABLE IF NOT EXISTS user_account (
    id_user       SERIAL PRIMARY KEY,
    email         VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    is_active     BOOLEAN DEFAULT TRUE,
    id_role       INTEGER NOT NULL REFERENCES role(id_role)
);

CREATE TABLE IF NOT EXISTS log_entry (
    id_log      SERIAL PRIMARY KEY,
    id_user     INTEGER REFERENCES user_account(id_user),
    action      VARCHAR(255) NOT NULL,
    ip_address  VARCHAR(45),
    user_agent  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS scan_result (
    id_scan        SERIAL PRIMARY KEY,
    scanned_at     TIMESTAMPTZ DEFAULT NOW(),
    image_name     VARCHAR(255) NOT NULL,
    image_tag      VARCHAR(100) NOT NULL,
    git_sha        VARCHAR(40),
    critical_count INTEGER DEFAULT 0,
    high_count     INTEGER DEFAULT 0,
    medium_count   INTEGER DEFAULT 0,
    low_count      INTEGER DEFAULT 0,
    status         VARCHAR(20) DEFAULT 'passed',
    raw_json       TEXT,
    triggered_by   VARCHAR(100) DEFAULT 'ci'
);

CREATE TABLE IF NOT EXISTS incident (
    id_incident       SERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ,
    type              VARCHAR(100) NOT NULL,
    title             VARCHAR(255) NOT NULL,
    severity          VARCHAR(20) DEFAULT 'high',
    status            VARCHAR(20) DEFAULT 'open',
    affected_resource VARCHAR(255),
    description       TEXT,
    timeline          TEXT,
    ioc               TEXT,
    id_user           INTEGER REFERENCES user_account(id_user)
);

CREATE TABLE IF NOT EXISTS mobile_scan (
    id_scan          SERIAL PRIMARY KEY,
    scanned_at       TIMESTAMPTZ DEFAULT NOW(),
    app_name         VARCHAR(255),
    package_name     VARCHAR(255),
    version          VARCHAR(50),
    platform         VARCHAR(20) DEFAULT 'android',
    file_name        VARCHAR(255),
    mobsf_hash       VARCHAR(64),
    security_score   INTEGER,
    critical_count   INTEGER DEFAULT 0,
    high_count       INTEGER DEFAULT 0,
    warning_count    INTEGER DEFAULT 0,
    info_count       INTEGER DEFAULT 0,
    status           VARCHAR(20) DEFAULT 'pending',
    raw_json         TEXT,
    dangerous_perms  TEXT,
    trackers         TEXT
);

CREATE TABLE IF NOT EXISTS ebios_project (
    id_project  SERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ,
    name        VARCHAR(255) NOT NULL,
    scope       TEXT,
    context     TEXT,
    status      VARCHAR(20) DEFAULT 'in_progress',
    id_author   INTEGER REFERENCES user_account(id_user)
);

CREATE TABLE IF NOT EXISTS ebios_asset (
    id_asset       SERIAL PRIMARY KEY,
    id_project     INTEGER NOT NULL REFERENCES ebios_project(id_project),
    name           VARCHAR(255) NOT NULL,
    type           VARCHAR(50),
    description    TEXT,
    critical_level INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS ebios_fear_event (
    id_event    SERIAL PRIMARY KEY,
    id_project  INTEGER NOT NULL REFERENCES ebios_project(id_project),
    id_asset    INTEGER REFERENCES ebios_asset(id_asset),
    impact      VARCHAR(100),
    description TEXT,
    gravity     INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS ebios_risk_source (
    id_source   SERIAL PRIMARY KEY,
    id_project  INTEGER NOT NULL REFERENCES ebios_project(id_project),
    name        VARCHAR(255) NOT NULL,
    category    VARCHAR(50),
    motivation  TEXT,
    resources   VARCHAR(100),
    pertinence  INTEGER DEFAULT 2
);

CREATE TABLE IF NOT EXISTS ebios_scenario (
    id_scenario      SERIAL PRIMARY KEY,
    id_project       INTEGER NOT NULL REFERENCES ebios_project(id_project),
    id_risk_source   INTEGER REFERENCES ebios_risk_source(id_source),
    id_fear_event    INTEGER REFERENCES ebios_fear_event(id_event),
    type             VARCHAR(20) DEFAULT 'strategic',
    title            VARCHAR(255) NOT NULL,
    description      TEXT,
    attack_path      TEXT,
    likelihood       INTEGER DEFAULT 2,
    gravity          INTEGER DEFAULT 2,
    risk_level       INTEGER DEFAULT 4,
    treatment        VARCHAR(20) DEFAULT 'reduce',
    measures         TEXT
);

CREATE TABLE IF NOT EXISTS forensic_report (
    id_report         SERIAL PRIMARY KEY,
    created_at        TIMESTAMPTZ DEFAULT NOW(),
    updated_at        TIMESTAMPTZ,
    title             VARCHAR(255) NOT NULL,
    status            VARCHAR(20) DEFAULT 'draft',
    id_incident       INTEGER REFERENCES incident(id_incident),
    executive_summary TEXT,
    findings          TEXT,
    recommendations   TEXT,
    id_author         INTEGER REFERENCES user_account(id_user)
);

-- Rôles
INSERT INTO role (name, description) VALUES
  ('admin', 'Administrateur — accès complet'),
  ('user',  'Utilisateur standard — lecture seule')
ON CONFLICT DO NOTHING;

-- Permissions
INSERT INTO permission (action, description) VALUES
  ('users:read',   'Lire la liste des utilisateurs'),
  ('users:write',  'Créer/modifier des utilisateurs'),
  ('users:delete', 'Désactiver des utilisateurs'),
  ('logs:read',    'Consulter les logs')
ON CONFLICT DO NOTHING;

-- Liaison rôle admin ↔ toutes les permissions
INSERT INTO role_permissions (id_role, id_permis)
SELECT r.id_role, p.id_permis
FROM role r, permission p
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- Liaison rôle user ↔ lecture seule
INSERT INTO role_permissions (id_role, id_permis)
SELECT r.id_role, p.id_permis
FROM role r, permission p
WHERE r.name = 'user' AND p.action = 'users:read'
ON CONFLICT DO NOTHING;

-- Utilisateur admin par défaut
-- Mot de passe : Admin1234! (bcrypt coût 12)
-- À CHANGER EN PRODUCTION via l'API /users/
INSERT INTO user_account (email, password_hash, id_role)
SELECT
  'admin@cloudsecops.dev',
  '$2b$12$3LHB1Og4N4GNyv8VE50EweAjGEEvj6bWLoF/LNjc7PkveQ4gm4SuS',
  id_role
FROM role WHERE name = 'admin'
ON CONFLICT DO NOTHING;
