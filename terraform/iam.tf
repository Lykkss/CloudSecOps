# ============================================================
# IAM — Rôles et policies moindre privilège
# Issue GitHub : #7
# Principe : chaque rôle n'a accès qu'à ce dont il a besoin
# Référentiel : CIS AWS Benchmark v1.5 — section 1 (IAM)
#               NIST SP 800-207 — Zero Trust (never trust, always verify)
# ============================================================

# --- Rôle IAM pour l'instance EC2 ---
# Trust policy : seul le service EC2 peut assumer ce rôle (pas un utilisateur humain)
resource "aws_iam_role" "ec2_role" {
  name        = "${var.project_name}-ec2-role"
  description = "Role IAM pour EC2 backend - moindre privilege"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect    = "Allow"
        Principal = { Service = "ec2.amazonaws.com" }
        Action    = "sts:AssumeRole"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ec2-role"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Policy IAM EC2 — accès minimal nécessaire ---
# Autorise uniquement : lecture S3 sur le bucket projet, écriture CloudWatch Logs, lecture SSM
# Interdit : toute action admin, IAM, création de ressources
resource "aws_iam_policy" "ec2_policy" {
  name        = "${var.project_name}-ec2-policy"
  description = "Policy moindre privilege pour EC2 backend"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowS3ReadProjectBucket"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          "arn:aws:s3:::${var.project_name}-*",
          "arn:aws:s3:::${var.project_name}-*/*"
        ]
      },
      {
        Sid    = "AllowCloudWatchLogs"
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "arn:aws:logs:${var.aws_region}:*:log-group:/aws/ec2/${var.project_name}*"
      },
      {
        Sid    = "AllowSSMReadOnly"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.project_name}/*"
      }
    ]
  })

  tags = {
    Name        = "${var.project_name}-ec2-policy"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Attachement policy → rôle ---
resource "aws_iam_role_policy_attachment" "ec2_policy_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.ec2_policy.arn
}

# --- Instance Profile ---
# Conteneur du rôle IAM qu'on attache à l'EC2
# (AWS requiert un instance profile, pas un rôle directement)
resource "aws_iam_instance_profile" "ec2_profile" {
  name = "${var.project_name}-ec2-profile"
  role = aws_iam_role.ec2_role.name

  tags = {
    Name        = "${var.project_name}-ec2-profile"
    Project     = var.project_name
    Environment = var.environment
  }
}
