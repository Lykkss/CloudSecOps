# Rapport d'Investigation Forensique — Compromission IAM

**Référence :** CSO-FOR-2026-001  
**Classification :** CONFIDENTIEL  
**Statut :** Final  
**Date :** 2026-04-20  
**Auteur :** Équipe SecOps – CloudSecOps  

---

## 1. Résumé Exécutif

Une clé d'accès AWS (IAM Access Key) a été exposée accidentellement dans un dépôt GitHub public. L'attaquant a exploité cette clé pour conduire une phase d'énumération IAM, tenter une élévation de privilèges, désactiver le trail CloudTrail, exfiltrer des objets S3 et créer un utilisateur backdoor. L'incident a été détecté grâce à une alarme CloudWatch sur les erreurs `AccessDenied`. Le temps de détection (MTTD) est estimé à **90 minutes**. Aucune donnée critique client n'a été compromise — les données affectées sont des logs d'audit internes.

---

## 2. Chronologie de l'Incident

| Heure (UTC) | Événement | Source de détection |
|---|---|---|
| T-120 min | Exposition de la clé AKIA… sur GitHub (commit public) | GitHub Secret Scanning Alert |
| T-110 min | Premier appel API depuis 185.220.101.42 (Tor exit node, DE) | CloudTrail |
| T-105 min | Énumération IAM — 47 appels ListUsers/ListRoles/ListPolicies | CloudTrail |
| T-95 min | Tentative d'élévation : AttachUserPolicy → AdministratorAccess | CloudTrail (AccessDenied) |
| T-90 min | Désactivation de CloudTrail (StopLogging) | Config Rule |
| T-85 min | Exfiltration S3 — 1 247 objets téléchargés | S3 Access Logs |
| T-70 min | Création d'utilisateur backdoor `svc-backup-tmp` + AccessKey | CloudTrail |
| T-60 min | Mouvement latéral — AssumeRole vers `cloud-secops-ec2-role` | CloudTrail |
| T-30 min | Alarme CloudWatch `UnauthorizedAPICalls` déclenchée | CloudWatch Alarms |
| T-0 | Incident déclaré — containment initié | SOC |

---

## 3. Indicateurs de Compromission (IOC)

| Type | Valeur | Contexte |
|---|---|---|
| IP Address | `185.220.101.42` | Tor exit node — source de tous les appels API |
| IAM User | `svc-backup-tmp` | Utilisateur backdoor créé par l'attaquant |
| Access Key | `AKIAIOSFODNN7EXAMPLE` | Clé originale exposée sur GitHub |
| S3 Prefix | `s3://cloud-secops-logs-dev/` | Bucket exfiltré (logs d'audit) |
| API Call | `StopLogging` | Tentative anti-forensic |
| User-Agent | `aws-cli/2.13.0 Python/3.11 Linux/5.15` | UA utilisé par l'attaquant |

---

## 4. Analyse Technique

### 4.1 Vecteur d'entrée

La clé d'accès `AKIAIOSFODNN7EXAMPLE` a été commitée dans le fichier `.env` d'un dépôt GitHub rendu public par erreur. GitHub Secret Scanning a émis une alerte, mais celle-ci n'a pas été traitée dans les délais.

### 4.2 Phase d'énumération

L'attaquant a utilisé la clé pour identifier la structure IAM du compte :

```
aws iam list-users
aws iam list-roles
aws iam list-policies --scope Local
aws sts get-caller-identity
```

Ces appels ont généré 47 entrées dans CloudTrail en moins de 3 minutes — un pattern typique de reconnaissance automatisée (outil : **Pacu** ou **aws-recon**).

### 4.3 Tentative d'élévation de privilèges

La politique `AdministratorAccess` a été refusée car la clé n'avait pas les droits `iam:AttachUserPolicy`. La SCP (Service Control Policy) configurée sur l'account a bloqué l'opération :

```
AccessDenied: User: arn:aws:iam::123456789012:user/cloudsecops-ci
is not authorized to perform: iam:AttachUserPolicy
```

### 4.4 Anti-forensic — Désactivation CloudTrail

L'appel `StopLogging` a interrompu la journalisation pendant **20 minutes** (T-90 à T-70). Les logs S3 ont pris le relais pour la détection de l'exfiltration. Une règle AWS Config `cloudtrail-enabled` a alerté le SOC.

### 4.5 Exfiltration S3

1 247 objets du bucket `cloud-secops-logs-dev` ont été téléchargés via des appels `GetObject` répétitifs. Les objets contenaient des logs d'audit (non classifiés). Aucune donnée PII ou secret métier n'était présente dans ce bucket.

### 4.6 Persistance — Utilisateur backdoor

L'attaquant a créé `svc-backup-tmp` avec une nouvelle paire de clés, anticipant la révocation de la clé initiale. Cet utilisateur a été désactivé lors du containment.

---

## 5. Constatations

| # | Sévérité | Constatation | Preuve |
|---|---|---|---|
| F-01 | CRITIQUE | Clé IAM exposée dans un dépôt GitHub public | Commit hash `a3f7c9d` — fichier `.env` |
| F-02 | ÉLEVÉE | CloudTrail désactivé sans alarme immédiate | 20 min de gap dans les logs CloudTrail |
| F-03 | ÉLEVÉE | Absence de MFA sur le compte IAM compromis | IAM Credential Report |
| F-04 | MOYENNE | Rotation de clés non configurée (> 90 jours) | IAM Credential Report — LastRotated: jamais |
| F-05 | MOYENNE | Politique IAM trop permissive (S3 GetObject *) | IAM Policy Analyzer |
| F-06 | FAIBLE | User-Agent non filtré — outils d'attaque non bloqués | CloudTrail — user-agent Pacu identifié |

---

## 6. Impact

| Domaine | Impact | Détail |
|---|---|---|
| Confidentialité | Modéré | 1 247 logs d'audit exfiltrés (non classifiés) |
| Intégrité | Faible | Aucune modification de données métier |
| Disponibilité | Faible | CloudTrail interrompu 20 min |
| Conformité | Élevé | Violation potentielle RGPD (Art. 33) si données personnelles |

---

## 7. Recommandations

### Immédiates (< 24h)

1. **Révoquer** toutes les clés IAM exposées et les sessions actives associées
2. **Désactiver** l'utilisateur backdoor `svc-backup-tmp` et supprimer ses clés
3. **Réactiver** CloudTrail et vérifier l'intégrité des logs S3
4. **Notifier** le DPO si des données personnelles sont présentes dans les objets exfiltrés

### Court terme (< 1 semaine)

5. **Activer MFA** obligatoire sur tous les comptes IAM humains (politique SCP)
6. **Implémenter la rotation automatique** des clés IAM (max 90 jours) via AWS Config
7. **Restreindre la politique S3** : principe du moindre privilège, préfixes spécifiques
8. **Configurer une alarme CloudWatch** sur `StopLogging` avec notification PagerDuty

### Long terme (< 1 mois)

9. **Migrer vers IAM Roles** pour toutes les workloads (supprimer les clés long-lived)
10. **Activer AWS GuardDuty** — détection automatique des patterns anormaux
11. **Mettre en place un SIEM** (AWS Security Hub + OpenSearch) pour corrélation des logs
12. **Former les équipes** aux bonnes pratiques de gestion des secrets (Vault, AWS Secrets Manager)

---

## 8. Leçons Apprises

| Problème | Cause racine | Correction |
|---|---|---|
| Exposition de la clé | Absence de pre-commit hook bloquant les secrets | Intégrer `gitleaks` dans la CI/CD |
| MTTD de 90 min | Alerte GitHub Scanning non monitorée | Intégrer les alertes dans le canal SecOps Slack |
| Gap de 20 min sans logs | Pas d'alarme sur StopLogging | CloudWatch Alarm + SNS sur `StopLogging` |
| Exfiltration non détectée | Pas de détection sur volume S3 anormal | GuardDuty S3 Protection activé |

---

## 9. Annexes

### A. Requête CloudTrail pour investigation

```bash
aws cloudtrail lookup-events \
  --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAIOSFODNN7EXAMPLE \
  --start-time 2026-04-20T00:00:00Z \
  --end-time 2026-04-20T02:00:00Z \
  --query 'Events[*].[EventTime,EventName,Username,SourceIPAddress]' \
  --output table
```

### B. Commandes de containment

```bash
# Révoquer la clé compromisee
aws iam delete-access-key --user-name cloudsecops-ci --access-key-id AKIAIOSFODNN7EXAMPLE

# Désactiver le backdoor
aws iam delete-access-key --user-name svc-backup-tmp --access-key-id <KEY_ID>
aws iam delete-user --user-name svc-backup-tmp

# Invalider les sessions actives
aws iam delete-user-policy --user-name cloudsecops-ci --policy-name *
aws sts assume-role --role-arn arn:aws:iam::123456789012:role/cloud-secops-ec2-role \
  --role-session-name forensic-audit  # vérifier les sessions actives
```

### C. Références

- NIST SP 800-61r2 — Computer Security Incident Handling Guide
- ISO/IEC 27035 — Information Security Incident Management
- CIS AWS Foundations Benchmark v1.5 — Section 1 (IAM)
- MITRE ATT&CK Cloud : T1552.005 (Cloud Instance Metadata API), T1537 (Transfer Data to Cloud Account)
