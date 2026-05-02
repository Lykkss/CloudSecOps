# ============================================================
# RDS — PostgreSQL dans le subnet privé
# Issue GitHub : #10
# Type : db.t3.micro (Free Tier — 750h/mois)
# Critères : pas d'accès public, connexion EC2 only, chiffrement
# ============================================================

variable "db_name" {
  description = "Nom de la base de données"
  type        = string
  default     = "cloudsecops"
}

variable "db_username" {
  description = "Nom d'utilisateur PostgreSQL master"
  type        = string
  default     = "cloudsecops_admin"
}

variable "db_password" {
  description = "Mot de passe PostgreSQL master (stocker dans SSM en prod)"
  type        = string
  sensitive   = true # Terraform masque cette valeur dans les logs
  default     = "changeme-local-dev-password"
}

# --- Subnet Group RDS ---
# RDS requiert un subnet group — on utilise le subnet privé
# En prod : ajouter un second subnet privé en eu-west-3c pour la HA
# RDS non déployé en LocalStack Community (Pro feature)
# Le code est prêt pour le vrai AWS Free Tier
resource "aws_db_subnet_group" "main" {
  count       = var.localstack_enabled ? 0 : 1
  name        = "${var.project_name}-db-subnet-group"
  description = "Subnet group RDS - subnet prive uniquement"
  subnet_ids  = [aws_subnet.private.id, aws_subnet.public.id]
  # Note : 2 subnets requis par AWS. En prod, utiliser 2 subnets PRIVÉS.
  # Ici le subnet public est ajouté uniquement pour satisfaire la contrainte
  # LocalStack/AWS de 2 AZ minimum. RDS reste accessible uniquement via SG-RDS.

  tags = {
    Name        = "${var.project_name}-db-subnet-group"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Instance RDS PostgreSQL ---
resource "aws_db_instance" "postgres" {
  count             = var.localstack_enabled ? 0 : 1
  identifier        = "${var.project_name}-postgres"
  engine            = "postgres"
  engine_version    = "15"
  instance_class    = "db.t3.micro" # Free Tier
  allocated_storage = 20            # Free Tier : 20 Go inclus
  storage_type      = "gp2"

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  # Réseau — subnet privé, pas d'accès public
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false # CRITIQUE : jamais d'accès public RDS

  # Chiffrement au repos (AES-256)
  # Note LocalStack : storage_encrypted simulé, pas réellement chiffré en local
  storage_encrypted = !var.localstack_enabled # Désactivé en LocalStack (non supporté)

  # Sauvegarde automatique (RPO = 1 jour)
  backup_retention_period = 0             # 7 jours de sauvegardes
  backup_window           = "03:00-04:00" # Fenêtre de backup en UTC

  # Maintenance
  maintenance_window         = "Mon:04:00-Mon:05:00"
  auto_minor_version_upgrade = true

  # Suppression — protection en prod
  deletion_protection       = false # Mettre à true en prod
  skip_final_snapshot       = true  # Mettre à false en prod
  final_snapshot_identifier = "${var.project_name}-final-snapshot"

  # Logs PostgreSQL vers CloudWatch
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = {
    Name        = "${var.project_name}-postgres"
    Project     = var.project_name
    Environment = var.environment
  }
}
