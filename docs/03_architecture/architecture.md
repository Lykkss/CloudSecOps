# Plan d'Architecture — CloudSecOps
## Architecture Cloud Native Sécurisée AWS

**Projet** : CloudSecOps  
**Auteur** : Lykkss  
**Version** : 1.0  
**Date** : 2026-04-11  
**Contexte** : Projet fil-rouge B3 Cybersécurité - Ynov Campus  

---

## Table des matières

1. [Vue d'ensemble](#1-vue-densemble)
2. [Architecture réseau](#2-architecture-réseau)
3. [Architecture applicative](#3-architecture-applicative)
4. [Architecture sécurité](#4-architecture-sécurité)
5. [Architecture DevSecOps](#5-architecture-devsecops)
6. [Modèle de données](#6-modèle-de-données)
7. [Flux de données](#7-flux-de-données)
8. [Infrastructure as Code](#8-infrastructure-as-code)
9. [Principes de sécurité](#9-principes-de-sécurité)
10. [Budget et contraintes](#10-budget-et-contraintes)
11. [Critères de réussite](#11-critères-de-réussite)

---

## 1. Vue d'ensemble

### 1.1 Contexte

CloudSecOps est une architecture Cloud Native sécurisée déployée sur AWS (région `eu-west-3` — Paris).  
Elle repose sur trois piliers extraits du cahier des charges :

| Pilier | Principe | Référentiel |
|---|---|---|
| **Security by Design** | La sécurité est intégrée dès la conception, pas ajoutée a posteriori | ISO 27001, ANSSI |
| **Infrastructure as Code** | Toute ressource est versionnée et reproductible via Terraform | CIS AWS Benchmark |
| **Zero Trust** | Aucun réseau ni utilisateur n'est implicitement de confiance | NIST SP 800-207 |

### 1.2 Acteurs du système

| Acteur | Rôle | Accès |
|---|---|---|
| Utilisateur final | Consomme l'API REST via HTTPS | Port 443 uniquement |
| Administrateur | Gère l'infrastructure et les utilisateurs | SSH restreint + IAM MFA |
| DevOps | Déploie via pipeline CI/CD | GitHub Actions → AWS |
| Analyste sécurité | Surveille les logs et répond aux incidents | CloudTrail + CloudWatch read-only |

### 1.3 Vue logique globale

```
Internet
    │
    │ HTTPS (TLS 1.2+)
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  AWS Region : eu-west-3 (Paris)                                 │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  VPC : 10.0.0.0/16                                       │   │
│  │                                                          │   │
│  │  ┌─────────────────────┐   ┌──────────────────────────┐ │   │
│  │  │  Subnet Public      │   │  Subnet Privé            │ │   │
│  │  │  10.0.1.0/24        │   │  10.0.2.0/24             │ │   │
│  │  │  eu-west-3a         │   │  eu-west-3b              │ │   │
│  │  │                     │   │                          │ │   │
│  │  │  ┌───────────────┐  │   │  ┌────────────────────┐  │ │   │
│  │  │  │  EC2 t3.micro │  │──▶│  │  RDS PostgreSQL     │  │ │   │
│  │  │  │  FastAPI      │  │   │  │  db.t3.micro       │  │ │   │
│  │  │  │  Docker       │  │   │  │  Port 5432          │  │ │   │
│  │  │  │  SG-EC2       │  │   │  │  SG-RDS            │  │ │   │
│  │  │  └───────────────┘  │   │  └────────────────────┘  │ │   │
│  │  └─────────────────────┘   └──────────────────────────┘ │   │
│  │            │                                             │   │
│  │  ┌─────────▼──────────────────────────────────────────┐ │   │
│  │  │  Internet Gateway          Route Tables            │ │   │
│  │  │  Public  → 0.0.0.0/0 → IGW                        │ │   │
│  │  │  Privé   → 10.0.0.0/16 local uniquement           │ │   │
│  │  └────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌──────────┐  ┌──────────────┐  ┌───────────┐  ┌──────────┐  │
│  │    S3    │  │  CloudTrail  │  │CloudWatch │  │   IAM    │  │
│  │ Chiffré  │  │  (audit API) │  │(monitoring│  │(rôles    │  │
│  │ AES-256  │  │  Multi-trail │  │ alertes)  │  │ moindre  │  │
│  └──────────┘  └──────────────┘  └───────────┘  │ privilège│  │
│                                                  └──────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Architecture réseau

### 2.1 VPC et segmentation

| Ressource | Valeur | Justification sécurité |
|---|---|---|
| VPC CIDR | `10.0.0.0/16` | Espace privé RFC 1918, isolé d'Internet |
| Subnet public | `10.0.1.0/24` — eu-west-3a | Zone DMZ : EC2 exposé avec SG restrictif |
| Subnet privé | `10.0.2.0/24` — eu-west-3b | Zone interne : RDS sans accès Internet |
| Internet Gateway | 1 IGW attaché au VPC | Seul point d'entrée Internet contrôlé |
| DNS Hostnames | Activé | Nécessaire pour les VPC Endpoints (sans IGW) |

> **Principe Zero Trust appliqué** : la segmentation réseau impose que RDS ne soit physiquement joignable que depuis le subnet public — même un attaquant ayant accès au VPC ne peut pas atteindre la base de données sans passer par le Security Group EC2.

### 2.2 Règles de routage

| Route Table | Destination | Target | Usage |
|---|---|---|---|
| `rt-public` | `10.0.0.0/16` | local | Trafic intra-VPC |
| `rt-public` | `0.0.0.0/0` | IGW | Accès Internet sortant (EC2) |
| `rt-private` | `10.0.0.0/16` | local | Trafic intra-VPC uniquement |

> Le subnet privé n'a **aucune route vers Internet** — RDS ne peut ni recevoir ni initier de connexion externe. (CIS AWS Benchmark 5.4)

### 2.3 Security Groups

#### SG-EC2 (backend)

| Direction | Port | Protocole | Source | Justification |
|---|---|---|---|---|
| Ingress | 443 | TCP | `0.0.0.0/0` | API publique HTTPS |
| Ingress | 80 | TCP | `0.0.0.0/0` | Redirection HTTP → HTTPS |
| Ingress | 22 | TCP | `admin_cidr` | SSH admin restreint |
| Egress | ALL | ALL | `0.0.0.0/0` | Accès services AWS |

#### SG-RDS (base de données)

| Direction | Port | Protocole | Source | Justification |
|---|---|---|---|---|
| Ingress | 5432 | TCP | `SG-EC2` | PostgreSQL — EC2 uniquement |
| Egress | ALL | ALL | `10.0.0.0/16` | Réponses intra-VPC uniquement |

> Référence **CIS AWS Benchmark 5.2** : aucun SG ne doit autoriser `0.0.0.0/0` sur des ports sensibles (5432, 3306, etc.).

---

## 3. Architecture applicative

### 3.1 EC2 — Backend API

| Paramètre | Valeur | Contrainte budget |
|---|---|---|
| Type | `t3.micro` | Free Tier (750h/mois) |
| OS | Amazon Linux 2023 | Maintenu par AWS, patches auto |
| Runtime | Docker (conteneur FastAPI) | Isolation applicative |
| IAM | Instance Profile `ec2-profile` | Pas de clés statiques |
| Stockage | EBS gp3 8 Go | Free Tier (30 Go inclus) |

```
EC2 t3.micro
└── Docker
    └── Conteneur FastAPI
        ├── Routes /auth  (JWT)
        ├── Routes /users (RBAC)
        ├── Routes /admin (rôle admin requis)
        └── Routes /health
```

### 3.2 RDS — Base de données

| Paramètre | Valeur | Contrainte budget |
|---|---|---|
| Moteur | PostgreSQL 15 | Open source, fiable |
| Type | `db.t3.micro` | Free Tier (750h/mois) |
| Stockage | 20 Go gp2 | Free Tier (20 Go inclus) |
| Accès public | **Désactivé** | Isolation réseau totale |
| Chiffrement | AES-256 (at rest) | CIS AWS Benchmark 2.3 |
| Subnet group | Subnet privé uniquement | Pas d'exposition Internet |
| Backup | 7 jours | RTO/RPO bas |

### 3.3 S3 — Stockage objets

| Paramètre | Valeur |
|---|---|
| Chiffrement | SSE-S3 (AES-256) |
| Block Public Access | Activé sur les 4 options |
| Versioning | Activé (logs CloudTrail) |
| Taille | ≤ 5 Go (Free Tier) |
| Usage | Logs CloudTrail + assets applicatifs |

---

## 4. Architecture sécurité

### 4.1 IAM — Gestion des identités

```
AWS Account
├── IAM Role : cloud-secops-ec2-role
│   ├── Trust Policy : ec2.amazonaws.com seulement
│   └── IAM Policy : cloud-secops-ec2-policy
│       ├── s3:GetObject / s3:ListBucket → cloud-secops-*
│       ├── logs:CreateLogGroup / PutLogEvents → /aws/ec2/cloud-secops*
│       └── ssm:GetParameter → /cloud-secops/*
│
└── IAM Instance Profile : cloud-secops-ec2-profile
    └── Attaché à l'EC2 (pas de clés statiques ACCESS_KEY)
```

**Principes appliqués (CIS AWS Benchmark section 1) :**
- Aucun accès administrateur global
- Rôles plutôt qu'utilisateurs IAM avec clés
- Rotation des clés (SSM Parameter Store pour les secrets)
- MFA obligatoire sur le compte root
- Pas de clé d'accès root active

### 4.2 CloudTrail — Traçabilité

| Paramètre | Valeur | Référentiel |
|---|---|---|
| Scope | Multi-region trail | CIS AWS Benchmark 3.1 |
| Storage | S3 dédié chiffré | CIS AWS Benchmark 3.6 |
| Log file validation | Activée | CIS AWS Benchmark 3.2 |
| Events | Management + Data events | Traçabilité complète |
| Retention | 90 jours minimum | ISO 27001 A.12.4 |

> CloudTrail enregistre **toutes les actions API AWS** : qui a fait quoi, quand, depuis quelle IP. C'est le socle de l'analyse forensique (Sprint 5).

### 4.3 CloudWatch — Monitoring et alertes

| Alarme | Métrique | Seuil | Action |
|---|---|---|---|
| CPU élevé | `CPUUtilization` | > 80% 5min | SNS notification |
| Connexions DB | `DatabaseConnections` | > 50 | SNS notification |
| Erreurs API | `5XXError` | > 10/min | SNS notification |
| Tentatives SSH | Logs `/var/log/auth` | Pattern `Failed password` | SNS notification |

### 4.4 Chiffrement

| Couche | Mécanisme | Standard |
|---|---|---|
| Transit (HTTPS) | TLS 1.2+ | OWASP ASVS V9 |
| Transit (DB) | SSL PostgreSQL | CIS AWS Benchmark 2.3 |
| Repos (RDS) | AES-256 KMS | CIS AWS Benchmark 2.3 |
| Repos (S3) | SSE-S3 AES-256 | CIS AWS Benchmark 2.1 |
| Secrets (JWT) | HS256 + SSM Parameter Store | OWASP ASVS V3 |

---

## 5. Architecture DevSecOps

### 5.1 Pipeline CI/CD

```
Developer
    │
    │ git push / pull request
    ▼
GitHub Repository (Lykkss/CloudSecOps)
    │
    ▼
GitHub Actions (déclenché au push sur main)
    │
    ├── Job 1 : SAST (SonarCloud)
    │   └── Analyse statique du code Python/FastAPI
    │   └── Quality gate : 0 vulnérabilité critique
    │
    ├── Job 2 : Scan dépendances
    │   └── pip-audit / safety
    │   └── Bloque si CVE critique détectée
    │
    ├── Job 3 : Build Docker
    │   └── docker build
    │   └── Trivy scan image
    │   └── Bloque si vulnérabilité CRITICAL ou HIGH
    │
    ├── Job 4 : Terraform validate + plan
    │   └── terraform validate
    │   └── terraform plan (dry run)
    │   └── Revue manuelle du plan
    │
    └── Job 5 : Deploy (sur approbation)
        └── terraform apply
        └── docker push → EC2
```

### 5.2 Outils de sécurité retenus

| Outil | Usage | Justification (veille techno) |
|---|---|---|
| **Trivy** | Scan image Docker | Open source, intégration native GitHub Actions, CVE DB à jour |
| **SonarCloud** | SAST code Python | Gratuit usage académique, règles OWASP intégrées |
| **pip-audit** | Scan dépendances Python | Officiel PyPA, simple à intégrer |
| **Terraform** | IaC + drift detection | Multi-cloud, modulaire, support AWS mature |
| **GitHub Actions** | Orchestration CI/CD | Intégration native, gratuit pour repos publics |

### 5.3 Quality Gates

Un déploiement est **bloqué** si :
- Vulnérabilité **CRITICAL** ou **HIGH** détectée par Trivy
- Score SonarCloud < seuil qualité (0 bug bloquant)
- `terraform validate` échoue
- Tests unitaires FastAPI en échec

---

## 6. Modèle de données

### 6.1 Schéma de base de données (PostgreSQL)

```
┌──────────────┐       ┌───────────────────┐       ┌──────────────┐
│     role     │       │   user_account    │       │  deployment  │
│──────────────│       │───────────────────│       │──────────────│
│ id_role   PK │◄──┐   │ id_user        PK │──────►│ id_deploy PK │
│ name         │   │   │ email            │       │ version      │
│ description  │   └───│ password_hash    │       │ git_ref      │
└──────────────┘       │ created_at       │       │ status       │
        │              │ is_active        │       │ deployed_at  │
        │              │ id_role       FK │       │ triggered_by │
        ▼              └───────────────────┘       └──────────────┘
┌──────────────┐               │
│  permission  │               │
│──────────────│               ▼
│ id_permis PK │       ┌──────────────┐       ┌──────────────┐
│ action       │       │  log_entry   │       │   incident   │
│ description  │       │──────────────│       │──────────────│
└──────────────┘       │ id_log    PK │       │ id_incident  │
        │              │ id_user   FK │       │ title        │
        ▼              │ action       │       │ description  │
┌──────────────────┐   │ ip_address   │       │ severity     │
│ role_permissions │   │ user_agent   │       │ status       │
│──────────────────│   │ created_at   │       │ detected_at  │
│ id_role       FK │   └──────────────┘       │ resolved_at  │
│ id_permis     FK │                          └──────────────┘
└──────────────────┘
```

### 6.2 Rôles RBAC

| Rôle | Permissions | Routes accessibles |
|---|---|---|
| `admin` | Toutes | `/admin/*`, `/users/*`, `/health` |
| `user` | Lecture seule | `/users/me`, `/health` |

---

## 7. Flux de données

### 7.1 Flux d'authentification (F01 — JWT)

```
Utilisateur          EC2/FastAPI           RDS PostgreSQL
    │                     │                      │
    │── POST /auth/login ─►│                      │
    │                     │── SELECT user ───────►│
    │                     │◄── user + hash ───────│
    │                     │                      │
    │                     │ [vérif bcrypt hash]   │
    │                     │ [génère JWT HS256]    │
    │                     │                      │
    │                     │── INSERT log_entry ──►│
    │◄── 200 {token} ─────│                      │
    │                     │                      │
```

### 7.2 Flux CI/CD (F04 — Terraform automatisé)

```
Developer            GitHub               GitHub Actions            AWS (LocalStack dev)
    │                   │                       │                         │
    │── git push ──────►│                       │                         │
    │                   │── trigger workflow ──►│                         │
    │                   │                       │── SAST scan             │
    │                   │                       │── Trivy scan            │
    │                   │                       │── terraform plan ───────►│
    │                   │                       │◄── plan output ─────────│
    │                   │◄── review required ───│                         │
    │── approve ────────►── approve ───────────►│                         │
    │                   │                       │── terraform apply ──────►│
    │                   │                       │◄── apply complete ──────│
    │                   │                       │── docker deploy ────────►│
```

### 7.3 Flux de détection d'incident (F05 — Sprint 5)

```
Attaque simulée       CloudTrail           CloudWatch            Analyste
    │                     │                    │                    │
    │── action IAM ───────►│                   │                    │
    │                     │── log API event ──►│                    │
    │                     │                    │── metric filter    │
    │                     │                    │── alarm trigger    │
    │                     │                    │── SNS notification►│
    │                     │                    │                    │
    │                     │◄────── analyse logs (Athena/manual) ───│
    │                     │                    │                    │
    │                     │───────────────── rapport forensique ───►│
```

---

## 8. Infrastructure as Code

### 8.1 Organisation Terraform actuelle

```
terraform/
├── provider.tf          # Provider AWS + config LocalStack dynamique
├── variables.tf         # Variables : région, projet, environnement, admin_cidr
├── main.tf              # VPC 10.0.0.0/16
├── network.tf           # Subnets, IGW, Route Tables, associations
├── security_groups.tf   # SG EC2 (443/80/22) + SG RDS (5432)
├── iam.tf               # Role, Policy, Instance Profile EC2
├── outputs.tf           # vpc_id, subnet ids, sg ids, profile name
├── localstack.tfvars    # Variables dev local (gitignored)
└── .terraform/          # Provider binaire (gitignored)
```

### 8.2 Extension prévue (Sprints 2-4)

```
terraform/
├── [existant Sprint 1]
├── ec2.tf               # Instance EC2 + user_data Docker
├── rds.tf               # RDS PostgreSQL + subnet group
├── s3.tf                # Bucket logs + chiffrement
├── cloudtrail.tf        # Trail multi-région
├── cloudwatch.tf        # Alarmes + log groups
└── modules/             # Modularisation (Sprint 4)
    ├── vpc/
    ├── compute/
    ├── database/
    └── security/
```

### 8.3 Gestion du state Terraform

| Environnement | Backend state | Sécurité |
|---|---|---|
| Dev local | Local (`terraform.tfstate`) | Gitignored, non partagé |
| CI/CD (futur) | S3 + DynamoDB lock | Chiffré, versionné, accès IAM restreint |

---

## 9. Principes de sécurité

### 9.1 Mapping exigences → implémentation

| Exigence cahier des charges | Implémentation technique | Référentiel |
|---|---|---|
| Séparation réseau stricte | Subnet public/privé + SG restrictifs | CIS AWS 5.2, NIST SP 800-207 |
| Chiffrement au repos (AES-256) | RDS KMS + S3 SSE-S3 | CIS AWS 2.1, 2.3 |
| Chiffrement en transit (TLS 1.2+) | HTTPS EC2 + SSL PostgreSQL | OWASP ASVS V9 |
| Moindre privilège IAM | Policy scoped S3/CloudWatch/SSM | CIS AWS 1.x, ISO 27001 A.9 |
| Journalisation exhaustive | CloudTrail multi-région + CloudWatch | CIS AWS 3.x, ISO 27001 A.12.4 |
| Authentification forte | JWT HS256 + bcrypt + RBAC | OWASP ASVS V2, V3 |
| DevSecOps intégré | Trivy + SonarCloud + pip-audit | OWASP DevSecOps Guide |
| Zero Trust | Vérification JWT à chaque requête, SG par SG | NIST SP 800-207 |
| Traçabilité incidents | CloudTrail → Athena → rapport forensique | ISO 27001 A.16 |

### 9.2 Exclusions de périmètre (cahier des charges)

| Exclu | Raison |
|---|---|
| Multi-région haute disponibilité | Hors budget Free Tier |
| SIEM externe avancé (Splunk, ELK) | Hors périmètre académique |
| Interface front-end complexe | Focus sécurité backend |
| WAF AWS | Payant — simulé via SG |
| GuardDuty | Payant — CloudTrail en substitution |

---

## 10. Budget et contraintes

### 10.1 Budget AWS — Free Tier uniquement

| Service | Limite Free Tier | Usage projet | Coût |
|---|---|---|---|
| EC2 t3.micro | 750h/mois (12 mois) | 1 instance | **0€** |
| RDS db.t3.micro | 750h/mois (12 mois) | 1 instance | **0€** |
| S3 | 5 Go / 20 000 req GET | Logs + assets | **0€** |
| CloudTrail | 1 trail gratuit | 1 multi-region trail | **0€** |
| CloudWatch | 10 métriques / 3 dashboards | Alarmes basiques | **0€** |
| **Total** | | | **0€** |

> Tout le développement et les tests se font sur **LocalStack** (simulation AWS locale).  
> Aucun `terraform apply` sur le vrai AWS sans validation explicite.

### 10.2 Outils — tous gratuits ou open source

| Outil | Licence | Usage |
|---|---|---|
| Terraform 1.6+ | BSL | IaC |
| LocalStack 3.4 | Apache 2.0 | Simulation AWS locale |
| Docker | Apache 2.0 | Conteneurisation |
| FastAPI | MIT | Backend API |
| PostgreSQL | PostgreSQL License | Base de données |
| GitHub Actions | Gratuit repos publics | CI/CD |
| Trivy | Apache 2.0 | Scan conteneurs |
| SonarCloud | Gratuit académique | SAST |
| OWASP ZAP | Apache 2.0 | DAST |

---

## 11. Critères de réussite

### 11.1 Critères techniques (par sprint)

| Sprint | Livrable | Critère de validation |
|---|---|---|
| S1 — Infra Base | VPC, Subnets, SG, IAM | `terraform apply` OK sur LocalStack |
| S2 — Infra App | EC2, RDS, S3, CloudTrail | Connectivité EC2→RDS validée |
| S3 — Backend | FastAPI, JWT, RBAC, PostgreSQL | Login + token + routes protégées |
| S4 — DevSecOps | GitHub Actions, Trivy, SAST | Pipeline bloque si vuln critique |
| S5 — Sécurité | Simulation IAM, CloudTrail, rapport | Timeline forensique reconstituée |

### 11.2 Critères de sécurité globaux

- [ ] Aucune clé AWS statique dans le code ou le repo git
- [ ] Aucun accès `0.0.0.0/0` sur RDS (port 5432)
- [ ] Tous les secrets dans SSM Parameter Store (pas dans `.env` en prod)
- [ ] CloudTrail actif avec validation d'intégrité des logs
- [ ] Pipeline CI/CD bloque sur vulnérabilité CRITICAL
- [ ] JWT expirant (≤ 30 min) avec refresh token
- [ ] Tous les mots de passe hashés bcrypt (coût ≥ 12)
- [ ] HTTPS uniquement en production (redirection 80 → 443)

### 11.3 Exigences non-fonctionnelles (cahier des charges)

| Exigence | Cible | Mesure |
|---|---|---|
| Disponibilité | 99% | CloudWatch uptime |
| Temps de réponse API | < 200 ms | CloudWatch latency |
| Logs horodatés | Oui (UTC) | CloudTrail timestamp |
| Séparation dev/prod | Oui | Variable `environment` Terraform |

---

## Références

| Référentiel | Domaine | URL |
|---|---|---|
| NIST SP 800-207 | Zero Trust Architecture | https://csrc.nist.gov/publications/detail/sp/800-207/final |
| CIS AWS Benchmark v1.5 | Sécurité Cloud AWS | https://www.cisecurity.org/benchmark/amazon_web_services |
| ISO/IEC 27001:2022 | Gestion sécurité information | https://www.iso.org/isoiec-27001-information-security.html |
| OWASP ASVS v4 | Sécurité applicative | https://owasp.org/www-project-application-security-verification-standard/ |
| OWASP DevSecOps Guide | Pipeline sécurisé | https://owasp.org/www-project-devsecops-guideline/ |
| ANSSI — Cloud | Recommandations infogérance | https://www.ssi.gouv.fr/guide/recommandations-de-securite-relatives-a-linfogérance/ |
