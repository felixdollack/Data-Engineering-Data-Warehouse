data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  public_subnets = {
    public_a = {
      cidr = var.public_subnet_a_cidr
      az   = data.aws_availability_zones.available.names[0]
    }
    public_b = {
      cidr = var.public_subnet_b_cidr
      az   = data.aws_availability_zones.available.names[1]
    }
  }
}

resource "aws_vpc" "warehouse" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "${var.project_name}-vpc" }
}

resource "aws_internet_gateway" "warehouse" {
  vpc_id = aws_vpc.warehouse.id
  tags   = { Name = "${var.project_name}-igw" }
}

resource "aws_subnet" "public" {
  for_each = local.public_subnets

  vpc_id                  = aws_vpc.warehouse.id
  cidr_block              = each.value.cidr
  availability_zone       = each.value.az
  map_public_ip_on_launch = true

  tags = { Name = "${var.project_name}-${each.key}" }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.warehouse.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.warehouse.id
  }

  tags = { Name = "${var.project_name}-public" }
}

resource "aws_route_table_association" "public" {
  for_each = aws_subnet.public

  subnet_id      = each.value.id
  route_table_id = aws_route_table.public.id
}

resource "aws_security_group" "redshift" {
  name        = "${var.project_name}-redshift"
  description = "Restrict Sparkify Redshift access to the configured client CIDR."
  vpc_id      = aws_vpc.warehouse.id

  ingress {
    description = "Redshift client access from the trusted CIDR only"
    protocol    = "tcp"
    from_port   = 5439
    to_port     = 5439
    cidr_blocks = [var.allowed_ingress_cidr]
  }

  egress {
    description = "Allow Redshift to reach S3 and AWS service endpoints"
    protocol    = "-1"
    from_port   = 0
    to_port     = 0
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${var.project_name}-redshift" }
}

resource "aws_redshift_subnet_group" "warehouse" {
  name        = "${var.project_name}-subnets"
  description = "Two public subnets for the Sparkify Redshift cluster."
  subnet_ids  = [for subnet in aws_subnet.public : subnet.id]

  tags = { Name = "${var.project_name}-subnets" }
}

resource "aws_iam_role" "redshift_s3_read" {
  name = "${var.project_name}-s3-read"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "redshift.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })

  tags = { Name = "${var.project_name}-s3-read" }
}

resource "aws_iam_role_policy" "redshift_s3_read" {
  name = "${var.project_name}-s3-read"
  role = aws_iam_role.redshift_s3_read.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ListSparkifyDatasetPrefixes"
        Effect   = "Allow"
        Action   = "s3:ListBucket"
        Resource = "arn:aws:s3:::udacity-dend"
        Condition = {
          StringLike = {
            "s3:prefix" = [
              "song_data", "song_data/*",
              "log_data", "log_data/*",
              "log_json_path.json"
            ]
          }
        }
      },
      {
        Sid    = "ReadSparkifyDatasetObjects"
        Effect = "Allow"
        Action = "s3:GetObject"
        Resource = [
          "arn:aws:s3:::udacity-dend/song_data/*",
          "arn:aws:s3:::udacity-dend/log_data/*",
          "arn:aws:s3:::udacity-dend/log_json_path.json"
        ]
      }
    ]
  })
}

resource "aws_redshift_cluster" "warehouse" {
  cluster_identifier                  = var.project_name
  database_name                       = var.database_name
  master_username                     = var.database_user
  manage_master_password              = true
  node_type                           = "dc2.large"
  cluster_type                        = "single-node"
  port                                = 5439
  encrypted                           = true
  publicly_accessible                 = true
  automated_snapshot_retention_period = 0
  skip_final_snapshot                 = true
  cluster_subnet_group_name           = aws_redshift_subnet_group.warehouse.name
  vpc_security_group_ids              = [aws_security_group.redshift.id]
  iam_roles                           = [aws_iam_role.redshift_s3_read.arn]

  depends_on = [
    aws_iam_role_policy.redshift_s3_read,
    aws_route_table_association.public
  ]

  tags = { Name = var.project_name }
}
