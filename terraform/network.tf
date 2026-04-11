# ============================================================
# RÉSEAU — Subnets, IGW, Route Tables
# Issues GitHub : #4 (Subnet Public), #5 (Subnet Private)
# ============================================================

# --- Subnet Public (issue #4) ---
# Héberge l'EC2 backend, accessible depuis Internet via l'IGW
# CIDR 10.0.1.0/24 = 254 hôtes disponibles
resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "${var.aws_region}a"
  map_public_ip_on_launch = true  # Les EC2 dans ce subnet reçoivent une IP publique

  tags = {
    Name        = "${var.project_name}-subnet-public"
    Project     = var.project_name
    Environment = var.environment
    Tier        = "public"
  }
}

# --- Subnet Privé (issue #5) ---
# Héberge RDS PostgreSQL — aucun accès direct depuis Internet
# CIDR 10.0.2.0/24 = 254 hôtes disponibles
resource "aws_subnet" "private" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "${var.aws_region}b"
  map_public_ip_on_launch = false  # Jamais d'IP publique sur le subnet privé

  tags = {
    Name        = "${var.project_name}-subnet-private"
    Project     = var.project_name
    Environment = var.environment
    Tier        = "private"
  }
}

# --- Internet Gateway ---
# Passerelle entre le VPC et Internet
# Attachée uniquement au subnet public via la route table
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-igw"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Route Table Publique ---
# Route 0.0.0.0/0 → IGW : tout le trafic sortant va sur Internet
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name        = "${var.project_name}-rt-public"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Route Table Privée ---
# Aucune route vers Internet — le trafic reste dans le VPC
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name        = "${var.project_name}-rt-private"
    Project     = var.project_name
    Environment = var.environment
  }
}

# --- Associations Route Tables ↔ Subnets ---
resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  subnet_id      = aws_subnet.private.id
  route_table_id = aws_route_table.private.id
}
