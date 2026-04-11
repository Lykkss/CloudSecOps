# ============================================================
# SECURITY GROUPS — EC2 et RDS
# Issue GitHub : #6
# Principe : moindre privilège — on autorise uniquement ce qui est nécessaire
# Référentiel : CIS AWS Benchmark v1.5 — section 5 (Networking)
# ============================================================

# --- Security Group EC2 (backend public) ---
# Autorise : HTTPS entrant (443), SSH restreint, tout sortant
# Interdit  : HTTP (80) non chiffré, accès 0.0.0.0/0 sur SSH
resource "aws_security_group" "ec2" {
  name        = "${var.project_name}-sg-ec2"
  description = "Security Group pour l'instance EC2 backend"
  vpc_id      = aws_vpc.main.id

  # HTTPS entrant depuis Internet (API publique)
  ingress {
    description = "HTTPS depuis Internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # SSH restreint à l'IP admin uniquement (à restreindre en prod avec var.admin_cidr)
  ingress {
    description = "SSH admin"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.admin_cidr]
  }

  # HTTP entrant — accepté uniquement pour redirection vers HTTPS
  ingress {
    description = "HTTP (redirection vers HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Tout le trafic sortant est autorisé (l'EC2 doit pouvoir contacter les services AWS)
  egress {
    description = "Tout le trafic sortant"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.project_name}-sg-ec2"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Security Group RDS (base de données privée) ---
# Autorise : PostgreSQL (5432) uniquement depuis le SG EC2
# Interdit  : tout accès depuis Internet, tout accès depuis d'autres sources
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-sg-rds"
  description = "Security Group pour RDS PostgreSQL — accès EC2 uniquement"
  vpc_id      = aws_vpc.main.id

  # PostgreSQL uniquement depuis l'EC2 (référence au SG EC2, pas à un CIDR)
  ingress {
    description     = "PostgreSQL depuis EC2 uniquement"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  # Sortant : uniquement vers le VPC (RDS ne contacte pas Internet)
  egress {
    description = "Trafic sortant interne VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]
  }

  tags = {
    Name        = "${var.project_name}-sg-rds"
    Project     = var.project_name
    Environment = var.environment
  }
}
