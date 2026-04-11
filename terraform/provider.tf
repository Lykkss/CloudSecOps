provider "aws" {
  region = var.aws_region

  # LocalStack — activer uniquement en dev local (var.localstack_enabled = true)
  # En prod, supprimer le bloc dynamic et laisser la résolution IAM standard.
  dynamic "endpoints" {
    for_each = var.localstack_enabled ? [1] : []
    content {
      ec2          = "http://localhost:4566"
      s3           = "http://s3.localhost.localstack.cloud:4566"
      iam          = "http://localhost:4566"
      sts          = "http://localhost:4566"
      cloudtrail   = "http://localhost:4566"
      cloudwatch   = "http://localhost:4566"
      cloudwatchlogs = "http://localhost:4566"
      rds          = "http://localhost:4566"
    }
  }

  # Credentials factices pour LocalStack (jamais en prod)
  access_key = var.localstack_enabled ? "test" : null
  secret_key = var.localstack_enabled ? "test" : null

  # Skip les vérifications inutiles en local
  skip_credentials_validation = var.localstack_enabled
  skip_metadata_api_check     = var.localstack_enabled
  skip_requesting_account_id  = var.localstack_enabled
}
