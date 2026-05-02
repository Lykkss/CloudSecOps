# ============================================================
# EC2 — Instance backend FastAPI
# Issue GitHub : #9
# Type : t3.micro (Free Tier — 750h/mois)
# ============================================================

# AMI Amazon Linux 2023 — variable pour LocalStack (AMI fictive)
# En prod : remplacer par l'AMI réelle via data source aws_ami
variable "ec2_ami" {
  description = "AMI ID pour l'instance EC2 (Amazon Linux 2023 en prod)"
  type        = string
  default     = "ami-0302f42a44bf53a45"
}

variable "ec2_instance_type" {
  description = "Type d'instance EC2"
  type        = string
  default     = "t3.micro" # Free Tier
}

variable "ec2_key_name" {
  description = "Nom de la clé SSH (laisser vide si pas d'accès SSH nécessaire)"
  type        = string
  default     = "cloud-secops-key"
}

# EC2 non déployée en LocalStack Community (AMI lookup non supporté)
# Le code est prêt pour le vrai AWS Free Tier (terraform apply sans localstack_enabled)
resource "aws_instance" "backend" {
  count                  = var.localstack_enabled ? 0 : 1
  ami                    = var.ec2_ami
  instance_type          = var.ec2_instance_type
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name
  key_name               = var.ec2_key_name != "" ? var.ec2_key_name : null

  # Pas d'IP publique associée automatiquement — on passe par l'IGW via le subnet
  associate_public_ip_address = true

  # Script de démarrage : installation Docker + lancement FastAPI
  user_data = <<-EOF
    #!/bin/bash
    set -e

    # Mise à jour système
    dnf update -y

    # Installation Docker
    dnf install -y docker
    systemctl enable docker
    systemctl start docker

    # Ajout utilisateur ec2-user au groupe docker
    usermod -aG docker ec2-user

    # Création du répertoire applicatif
    mkdir -p /opt/cloudsecops

    # Le conteneur FastAPI sera déployé par le pipeline CI/CD (Sprint 4)
    echo "EC2 CloudSecOps backend prêt" > /opt/cloudsecops/status.txt
  EOF

  # Stockage EBS — 8 Go gp3 (Free Tier : 30 Go inclus)
  root_block_device {
    volume_type           = "gp3"
    volume_size           = 8
    encrypted             = true # Chiffrement EBS activé
    delete_on_termination = true
  }

  tags = {
    Name        = "${var.project_name}-ec2-backend"
    Project     = var.project_name
    Environment = var.environment
    Role        = "backend"
  }
}
