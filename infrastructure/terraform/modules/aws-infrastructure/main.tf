# DORA Compliance System - AWS Infrastructure Module
# Core AWS networking and security infrastructure

# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc"
    Type = "vpc"
  })
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-igw"
    Type = "internet-gateway"
  })
}

# Data source for availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# Calculate subnet CIDRs
locals {
  azs                = slice(data.aws_availability_zones.available.names, 0, 3)
  public_subnets     = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 1)]
  private_subnets    = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 11)]
  database_subnets   = [for i, az in local.azs : cidrsubnet(var.vpc_cidr, 8, i + 21)]
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(local.azs)
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = local.public_subnets[count.index]
  availability_zone       = local.azs[count.index]
  map_public_ip_on_launch = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-${local.azs[count.index]}"
    Type = "public-subnet"
    Tier = "public"
    "kubernetes.io/role/elb" = "1"
    "kubernetes.io/cluster/${var.name_prefix}-cluster" = "shared"
  })
}

# Private Subnets (for applications)
resource "aws_subnet" "private" {
  count = length(local.azs)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.private_subnets[count.index]
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-${local.azs[count.index]}"
    Type = "private-subnet"
    Tier = "private"
    "kubernetes.io/role/internal-elb" = "1"
    "kubernetes.io/cluster/${var.name_prefix}-cluster" = "shared"
  })
}

# Database Subnets (isolated)
resource "aws_subnet" "database" {
  count = length(local.azs)
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = local.database_subnets[count.index]
  availability_zone = local.azs[count.index]
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-${local.azs[count.index]}"
    Type = "database-subnet"
    Tier = "database"
  })
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = length(local.azs)
  
  domain = "vpc"
  
  depends_on = [aws_internet_gateway.main]
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-${local.azs[count.index]}"
    Type = "elastic-ip"
  })
}

# NAT Gateways
resource "aws_nat_gateway" "main" {
  count = length(local.azs)
  
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
  
  depends_on = [aws_internet_gateway.main]
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nat-${local.azs[count.index]}"
    Type = "nat-gateway"
  })
}

# Route Tables

# Public Route Table
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-public-rt"
    Type = "route-table"
    Tier = "public"
  })
}

# Private Route Tables (one per AZ for HA)
resource "aws_route_table" "private" {
  count = length(local.azs)
  
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main[count.index].id
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-rt-${local.azs[count.index]}"
    Type = "route-table"
    Tier = "private"
  })
}

# Database Route Table (no internet access)
resource "aws_route_table" "database" {
  vpc_id = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-rt"
    Type = "route-table"
    Tier = "database"
  })
}

# Route Table Associations

# Public subnet associations
resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private subnet associations
resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# Database subnet associations
resource "aws_route_table_association" "database" {
  count = length(aws_subnet.database)
  
  subnet_id      = aws_subnet.database[count.index].id
  route_table_id = aws_route_table.database.id
}

# Security Groups

# Default security group for VPC
resource "aws_security_group" "default" {
  name_prefix = "${var.name_prefix}-default-"
  vpc_id      = aws_vpc.main.id
  description = "Default security group for ${var.name_prefix} VPC"
  
  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  # Allow inbound traffic from VPC
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [aws_vpc.main.cidr_block]
    description = "All traffic from VPC"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-default-sg"
    Type = "security-group"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# ALB security group
resource "aws_security_group" "alb" {
  name_prefix = "${var.name_prefix}-alb-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for Application Load Balancer"
  
  # HTTP
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP from internet"
  }
  
  # HTTPS
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS from internet"
  }
  
  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
    Type = "security-group"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# Database security group
resource "aws_security_group" "database" {
  name_prefix = "${var.name_prefix}-db-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for database access"
  
  # PostgreSQL
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "PostgreSQL from application"
  }
  
  # Redis
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "Redis from application"
  }
  
  # MongoDB/DocumentDB
  ingress {
    from_port       = 27017
    to_port         = 27017
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "MongoDB from application"
  }
  
  # InfluxDB
  ingress {
    from_port       = 8086
    to_port         = 8086
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "InfluxDB from application"
  }
  
  # Neo4j
  ingress {
    from_port       = 7687
    to_port         = 7687
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "Neo4j Bolt from application"
  }
  
  # Neo4j HTTP
  ingress {
    from_port       = 7474
    to_port         = 7474
    protocol        = "tcp"
    security_groups = [aws_security_group.default.id]
    description     = "Neo4j HTTP from application"
  }
  
  # All outbound
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-sg"
    Type = "security-group"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# VPC Flow Logs
resource "aws_flow_log" "vpc" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.main.id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc-flow-log"
    Type = "flow-log"
  })
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/flowlogs/${var.name_prefix}"
  retention_in_days = 30
  kms_key_id        = var.kms_key_id
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc-flow-log-group"
    Type = "log-group"
  })
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "flow_log" {
  name_prefix = "${var.name_prefix}-flow-log-"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "vpc-flow-logs.amazonaws.com"
        }
      }
    ]
  })
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-flow-log-role"
    Type = "iam-role"
  })
}

# IAM Policy for VPC Flow Logs
resource "aws_iam_role_policy" "flow_log" {
  name_prefix = "${var.name_prefix}-flow-log-"
  role        = aws_iam_role.flow_log.id
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Effect = "Allow"
        Resource = "*"
      }
    ]
  })
}

# VPC Endpoints for AWS Services
resource "aws_vpc_endpoint" "s3" {
  vpc_id       = aws_vpc.main.id
  service_name = "com.amazonaws.${data.aws_region.current.name}.s3"
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-s3-endpoint"
    Type = "vpc-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_dkr" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.dkr"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  private_dns_enabled = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecr-dkr-endpoint"
    Type = "vpc-endpoint"
  })
}

resource "aws_vpc_endpoint" "ecr_api" {
  vpc_id              = aws_vpc.main.id
  service_name        = "com.amazonaws.${data.aws_region.current.name}.ecr.api"
  vpc_endpoint_type   = "Interface"
  subnet_ids          = aws_subnet.private[*].id
  security_group_ids  = [aws_security_group.vpc_endpoint.id]
  private_dns_enabled = true
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-ecr-api-endpoint"
    Type = "vpc-endpoint"
  })
}

# Security group for VPC endpoints
resource "aws_security_group" "vpc_endpoint" {
  name_prefix = "${var.name_prefix}-vpc-endpoint-"
  vpc_id      = aws_vpc.main.id
  description = "Security group for VPC endpoints"
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [aws_vpc.main.cidr_block]
    description = "HTTPS from VPC"
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpc-endpoint-sg"
    Type = "security-group"
  })
  
  lifecycle {
    create_before_destroy = true
  }
}

# Data source for current region
data "aws_region" "current" {}

# Network ACLs for additional security
resource "aws_network_acl" "private" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.private[*].id
  
  # Allow all inbound from VPC
  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = aws_vpc.main.cidr_block
    from_port  = 0
    to_port    = 0
  }
  
  # Allow all outbound
  egress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 0
    to_port    = 0
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-private-nacl"
    Type = "network-acl"
  })
}

resource "aws_network_acl" "database" {
  vpc_id     = aws_vpc.main.id
  subnet_ids = aws_subnet.database[*].id
  
  # Allow inbound from private subnets only
  ingress {
    protocol   = "-1"
    rule_no    = 100
    action     = "allow"
    cidr_block = "10.0.11.0/24"  # Private subnet 1
    from_port  = 0
    to_port    = 0
  }
  
  ingress {
    protocol   = "-1"
    rule_no    = 110
    action     = "allow"
    cidr_block = "10.0.12.0/24"  # Private subnet 2
    from_port  = 0
    to_port    = 0
  }
  
  ingress {
    protocol   = "-1"
    rule_no    = 120
    action     = "allow"
    cidr_block = "10.0.13.0/24"  # Private subnet 3
    from_port  = 0
    to_port    = 0
  }
  
  # Allow limited outbound (for patches and updates)
  egress {
    protocol   = "tcp"
    rule_no    = 100
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 443
    to_port    = 443
  }
  
  egress {
    protocol   = "tcp"
    rule_no    = 110
    action     = "allow"
    cidr_block = "0.0.0.0/0"
    from_port  = 80
    to_port    = 80
  }
  
  # Allow responses back to private subnets
  egress {
    protocol   = "-1"
    rule_no    = 200
    action     = "allow"
    cidr_block = "10.0.11.0/24"
    from_port  = 0
    to_port    = 0
  }
  
  egress {
    protocol   = "-1"
    rule_no    = 210
    action     = "allow"
    cidr_block = "10.0.12.0/24"
    from_port  = 0
    to_port    = 0
  }
  
  egress {
    protocol   = "-1"
    rule_no    = 220
    action     = "allow"
    cidr_block = "10.0.13.0/24"
    from_port  = 0
    to_port    = 0
  }
  
  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-nacl"
    Type = "network-acl"
  })
} 