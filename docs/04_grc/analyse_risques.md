# Analyse des Risques — CloudSecOps

**Version :** 1.0  
**Date :** 2026-04-20  
**Référentiel :** ISO/IEC 27005 + CIS AWS Benchmark v1.5  

---

## 1. Méthode d'évaluation

Chaque risque est évalué sur deux axes :

- **Probabilité** : 1 (rare) → 4 (presque certain)
- **Impact** : 1 (négligeable) → 4 (critique)
- **Score = Probabilité × Impact** — Seuil d'acceptabilité : ≤ 4

| Score | Niveau | Traitement |
|---|---|---|
| 1–4   | Faible    | Surveiller |
| 6–9   | Moyen     | Atténuer |
| 10–16 | Élevé     | Traiter en priorité |

---

## 2. Registre des risques

| ID | Risque | Probabilité | Impact | Score | Traitement | Contrôle |
|---|---|:---:|:---:|:---:|---|---|
| R-01 | Exposition de clés IAM dans le code source | 3 | 4 | **12 🔴** | Réduire | gitleaks CI, pre-commit hooks |
| R-02 | Accès non autorisé à la base de données RDS | 2 | 4 | **8 🟠** | Réduire | SG strict (port 5432 depuis EC2 uniquement), chiffrement at-rest |
| R-03 | Compromission du token JWT | 2 | 3 | **6 🟠** | Réduire | Expiration 30 min, SECRET_KEY ≥ 32 chars, rotation |
| R-04 | Élévation de privilèges IAM | 2 | 4 | **8 🔴** | Réduire | SCP, politique least-privilege, MFA obligatoire |
| R-05 | Exfiltration de données S3 | 2 | 3 | **6 🟠** | Réduire | Block Public Access, bucket policy CloudTrail uniquement |
| R-06 | Injection SQL via l'API | 1 | 4 | **4 🟡** | Surveiller | ORM SQLAlchemy (requêtes paramétrées), pas de requêtes brutes |
| R-07 | Déni de service (rate limiting absent) | 3 | 2 | **6 🟠** | Réduire | WAF AWS, rate limiting Uvicorn/nginx |
| R-08 | Image Docker avec CVE critiques | 3 | 3 | **9 🔴** | Réduire | Trivy scan CI, python:3.12-slim minimal |
| R-09 | Perte de disponibilité RDS | 1 | 3 | **3 🟢** | Accepter | Multi-AZ en prod, backup 7 jours |
| R-10 | Fuite de logs CloudTrail | 1 | 3 | **3 🟢** | Accepter | Bucket privé, chiffrement SSE-AES256, versioning |
| R-11 | Brute force sur l'endpoint /auth/login | 3 | 2 | **6 🟠** | Réduire | Message d'erreur générique (anti-enum), future : account lockout |
| R-12 | Token de longue durée en localStorage | 2 | 2 | **4 🟡** | Surveiller | Expiration 30 min, HttpOnly cookie en prod |

---

## 3. Plan de traitement des risques prioritaires

### R-01 — Exposition de clés IAM (Score 12)

**Contrôles en place :**
- `.gitignore` : `*.env`, `*.tfvars`, `localstack.tfvars`
- CI/CD : step de vérification de secrets (à implémenter : gitleaks)
- `terraform/variables.tf` : `db_password` marqué `sensitive = true`

**Contrôles à implémenter :**
```yaml
# .github/workflows/ci.yml — ajouter
- name: Scan secrets (gitleaks)
  uses: gitleaks/gitleaks-action@v2
  env:
    GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

### R-04 — Élévation de privilèges IAM (Score 8)

**Contrôles en place :**
- Politique IAM EC2 : S3 read uniquement sur `cloud-secops-*`, CloudWatch logs, SSM GetParameter
- Aucun droit `iam:*` accordé

**Contrôles à implémenter :**
- SCP (Service Control Policy) bloquant `iam:AttachUserPolicy` et `iam:CreateUser` pour les rôles non-admin
- AWS CloudTrail avec alarme CloudWatch sur les actions IAM sensibles

### R-08 — CVE dans l'image Docker (Score 9)

**Contrôles en place :**
- Base image `python:3.12-slim` (surface réduite)
- Trivy scan dans la CI sur chaque push
- Résultats visibles dans la webapp et GitHub Security tab

---

## 4. Déclaration d'Applicabilité (ISO 27001 — Annexe A — extrait)

| Contrôle ISO 27001:2022 | Applicable | Statut | Justification |
|---|:---:|---|---|
| A.8.5 — Authentification sécurisée | ✅ | Implémenté | JWT HS256, bcrypt coût 12 |
| A.8.15 — Journalisation | ✅ | Implémenté | LogEntry en DB, CloudTrail |
| A.8.24 — Cryptographie | ✅ | Implémenté | bcrypt, JWT, AES-256 S3/RDS |
| A.5.15 — Contrôle d'accès | ✅ | Implémenté | RBAC admin/user |
| A.8.8 — Gestion des vulnérabilités | ✅ | Implémenté | Trivy CI, résultats dans webapp |
| A.5.26 — Réponse aux incidents | ✅ | Implémenté | Simulation IAM, rapport forensique |
| A.8.20 — Sécurité des réseaux | ✅ | Implémenté | VPC, SG strict, pas d'accès public RDS |
| A.8.12 — Prévention fuites données | 🟡 | Partiel | Block S3 Public Access — DLP non implémenté |
| A.8.16 — Supervision | 🟡 | Partiel | CloudWatch (prod) — SIEM non implémenté |
| A.5.14 — Transfert d'information | ❌ | N/A | Hors périmètre projet académique |
