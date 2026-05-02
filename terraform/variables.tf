variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "cloud-secops"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "localstack_enabled" {
  description = "Activer les endpoints LocalStack pour le dev local"
  type        = bool
  default     = false
}

variable "admin_cidr" {
  description = "CIDR autorisé pour SSH admin (ex: votre IP publique /32)"
  type        = string
  default     = "0.0.0.0/0"  # A restreindre en prod à votre IP : "X.X.X.X/32"
}

