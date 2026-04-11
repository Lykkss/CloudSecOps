output "vpc_id" {
  description = "ID du VPC principal"
  value       = aws_vpc.main.id
}

output "subnet_public_id" {
  description = "ID du subnet public (EC2)"
  value       = aws_subnet.public.id
}

output "subnet_private_id" {
  description = "ID du subnet privé (RDS)"
  value       = aws_subnet.private.id
}

output "sg_ec2_id" {
  description = "ID du Security Group EC2"
  value       = aws_security_group.ec2.id
}

output "sg_rds_id" {
  description = "ID du Security Group RDS"
  value       = aws_security_group.rds.id
}

output "ec2_instance_profile_name" {
  description = "Nom de l'instance profile IAM à attacher à l'EC2"
  value       = aws_iam_instance_profile.ec2_profile.name
}

output "ec2_public_ip" {
  description = "IP publique de l'instance EC2 backend (vide en LocalStack)"
  value       = length(aws_instance.backend) > 0 ? aws_instance.backend[0].public_ip : "non déployé en LocalStack"
}

output "ec2_instance_id" {
  description = "ID de l'instance EC2 (vide en LocalStack)"
  value       = length(aws_instance.backend) > 0 ? aws_instance.backend[0].id : "non déployé en LocalStack"
}

output "rds_endpoint" {
  description = "Endpoint RDS PostgreSQL (vide en LocalStack)"
  value       = length(aws_db_instance.postgres) > 0 ? aws_db_instance.postgres[0].endpoint : "non déployé en LocalStack"
  sensitive   = true
}

output "s3_logs_bucket" {
  description = "Nom du bucket S3 des logs CloudTrail"
  value       = aws_s3_bucket.logs.bucket
}

output "cloudtrail_name" {
  description = "Nom du trail CloudTrail (vide en LocalStack)"
  value       = length(aws_cloudtrail.main) > 0 ? aws_cloudtrail.main[0].name : "non déployé en LocalStack"
}
