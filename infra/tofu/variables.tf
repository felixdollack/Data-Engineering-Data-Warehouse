variable "aws_profile" {
  description = "AWS CLI profile used by OpenTofu. Keep this separate from work credentials."
  type        = string
  default     = "sparkify"
}

variable "aws_region" {
  description = "AWS region in which to create the warehouse."
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Lowercase name prefix for the Redshift cluster and related resources."
  type        = string
  default     = "sparkify-dwh"

  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{2,62}$", var.project_name))
    error_message = "project_name must be 3-63 lowercase letters, digits, or hyphens and start with a letter."
  }
}

variable "database_name" {
  description = "Initial database name created in Redshift."
  type        = string
  default     = "dev"
}

variable "database_user" {
  description = "Redshift administrative username."
  type        = string
  default     = "awsuser"
}

variable "allowed_ingress_cidr" {
  description = "Single trusted IPv4 CIDR allowed to connect to Redshift, usually your_public_ip/32."
  type        = string

  validation {
    condition     = can(cidrnetmask(var.allowed_ingress_cidr)) && !strcontains(var.allowed_ingress_cidr, "/0")
    error_message = "Set a valid, restricted IPv4 CIDR. Do not expose Redshift to 0.0.0.0/0."
  }
}

variable "vpc_cidr" {
  description = "Private address range for the new project VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "public_subnet_a_cidr" {
  description = "CIDR for the first public Redshift subnet."
  type        = string
  default     = "10.42.1.0/24"
}

variable "public_subnet_b_cidr" {
  description = "CIDR for the second public Redshift subnet."
  type        = string
  default     = "10.42.2.0/24"
}
