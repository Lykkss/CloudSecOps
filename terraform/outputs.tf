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
