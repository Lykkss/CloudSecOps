# ============================================================
# S3 — Bucket sécurisé pour logs CloudTrail et assets
# Issue GitHub : #11
# Critères : chiffrement AES-256, Block Public Access activé
# Free Tier : 5 Go / 20 000 requêtes GET / 2 000 requêtes PUT
# ============================================================

# --- Bucket S3 principal (logs CloudTrail) ---
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}"

  tags = {
    Name        = "${var.project_name}-logs"
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "cloudtrail-logs"
  }
}

# --- Chiffrement SSE-S3 (AES-256) ---
# CIS AWS Benchmark 2.1.1 : chiffrement obligatoire sur tous les buckets
resource "aws_s3_bucket_server_side_encryption_configuration" "logs" {
  bucket = aws_s3_bucket.logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256" # SSE-S3 gratuit (SSE-KMS = payant)
    }
    bucket_key_enabled = true
  }
}

# --- Block Public Access — 4 options activées ---
# CIS AWS Benchmark 2.1.5 : aucun bucket ne doit être public
resource "aws_s3_bucket_public_access_block" "logs" {
  bucket = aws_s3_bucket.logs.id

  block_public_acls       = true # Bloque les nouvelles ACLs publiques
  block_public_policy     = true # Bloque les politiques de bucket publiques
  ignore_public_acls      = true # Ignore les ACLs publiques existantes
  restrict_public_buckets = true # Restreint l'accès aux buckets publics
}

# --- Versioning ---
# Permet de récupérer les logs supprimés accidentellement (intégrité forensique)
resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

# --- Politique de cycle de vie ---
# Non déployé en LocalStack (non supporté dans la version Community)
# Activé uniquement en prod (localstack_enabled = false)
resource "aws_s3_bucket_lifecycle_configuration" "logs" {
  count  = var.localstack_enabled ? 0 : 1
  bucket = aws_s3_bucket.logs.id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = 90
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# --- Bucket policy — accès CloudTrail uniquement ---
# CloudTrail a besoin de droits pour écrire dans ce bucket
resource "aws_s3_bucket_policy" "logs" {
  bucket = aws_s3_bucket.logs.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudTrailCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.logs.arn
      },
      {
        Sid    = "AllowCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.logs.arn}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      }
    ]
  })

  # La policy doit être appliquée après le Block Public Access
  depends_on = [aws_s3_bucket_public_access_block.logs]
}
