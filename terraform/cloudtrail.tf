# ============================================================
# CLOUDTRAIL — Journalisation de toutes les actions API AWS
# Issue GitHub : #12
# Critères : logs générés, bucket dédié
# Référentiel : CIS AWS Benchmark section 3 (Logging)
# ============================================================

# --- CloudWatch Log Group pour CloudTrail ---
# Permet de créer des alarmes sur les événements CloudTrail
resource "aws_cloudwatch_log_group" "cloudtrail" {
  name              = "/aws/cloudtrail/${var.project_name}"
  retention_in_days = 90 # Conservation 90 jours (ISO 27001 A.12.4)

  tags = {
    Name        = "${var.project_name}-cloudtrail-logs"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Rôle IAM pour CloudTrail → CloudWatch ---
# CloudTrail a besoin de droits pour écrire dans CloudWatch Logs
resource "aws_iam_role" "cloudtrail_cloudwatch" {
  name = "${var.project_name}-cloudtrail-cw-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "cloudtrail.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = {
    Name        = "${var.project_name}-cloudtrail-cw-role"
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  name = "${var.project_name}-cloudtrail-cw-policy"
  role = aws_iam_role.cloudtrail_cloudwatch.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ]
      Resource = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
    }]
  })
}

# --- Trail CloudTrail ---
# CIS AWS Benchmark 3.1 : activer un trail multi-région
# CIS AWS Benchmark 3.2 : activer la validation d'intégrité des logs
# CloudTrail non déployé en LocalStack Community (Pro feature)
resource "aws_cloudtrail" "main" {
  count = var.localstack_enabled ? 0 : 1
  name                          = "${var.project_name}-trail"
  s3_bucket_name                = aws_s3_bucket.logs.id
  s3_key_prefix                 = "cloudtrail"
  include_global_service_events = true  # Capture IAM, STS, etc. (services globaux)
  is_multi_region_trail         = true  # CIS 3.1 : surveillance toutes les régions
  enable_log_file_validation    = true  # CIS 3.2 : détection de tampering sur les logs
  enable_logging                = true

  # Export vers CloudWatch Logs pour les alarmes en temps réel
  cloud_watch_logs_group_arn = "${aws_cloudwatch_log_group.cloudtrail.arn}:*"
  cloud_watch_logs_role_arn  = aws_iam_role.cloudtrail_cloudwatch.arn

  # Data events S3


  # Capture des événements de gestion (create/delete/modify)
  event_selector {
    read_write_type           = "All" # Lecture ET écriture
    include_management_events = true

    # Capture des accès S3 (Data Events) — utile pour forensic
    data_resource {
      type   = "AWS::S3::Object"
      values = ["${aws_s3_bucket.logs.arn}/"]
    }
  }

  tags = {
    Name        = "${var.project_name}-trail"
    Project     = var.project_name
    Environment = var.environment
  }

  depends_on = [
    aws_s3_bucket_policy.logs,
    aws_iam_role_policy.cloudtrail_cloudwatch
  ]
}

# --- Alarmes CloudWatch sur événements critiques ---
# Non déployées en LocalStack (metric alarms partiellement supportées)
# Activées uniquement en prod (localstack_enabled = false)

resource "aws_cloudwatch_metric_alarm" "cloudtrail_changes" {
  count               = var.localstack_enabled ? 0 : 1
  alarm_name          = "${var.project_name}-cloudtrail-changes"
  alarm_description   = "Alerte : modification ou désactivation du trail CloudTrail"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "CloudTrailEventCount"
  namespace           = "CloudTrailMetrics"
  period              = 300
  statistic           = "Sum"
  threshold           = 1

  dimensions = {
    TrailName = aws_cloudtrail.main[0].name
  }

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

resource "aws_cloudwatch_metric_alarm" "unauthorized_api_calls" {
  count               = var.localstack_enabled ? 0 : 1
  alarm_name          = "${var.project_name}-unauthorized-api-calls"
  alarm_description   = "Alerte : appels API non autorisés détectés (AccessDenied)"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "UnauthorizedAttemptCount"
  namespace           = "CloudTrailMetrics"
  period              = 300
  statistic           = "Sum"
  threshold           = 5

  tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}
