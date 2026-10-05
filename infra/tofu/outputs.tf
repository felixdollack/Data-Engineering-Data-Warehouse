output "redshift_host" {
  description = "Hostname to put in dwh.cfg as CLUSTER.HOST."
  value       = aws_redshift_cluster.warehouse.dns_name
}

output "redshift_port" {
  description = "Port to put in dwh.cfg as CLUSTER.DB_PORT."
  value       = aws_redshift_cluster.warehouse.port
}

output "redshift_database" {
  description = "Database name to put in dwh.cfg as CLUSTER.DB_NAME."
  value       = aws_redshift_cluster.warehouse.database_name
}

output "redshift_username" {
  description = "Username to put in dwh.cfg as CLUSTER.DB_USER."
  value       = aws_redshift_cluster.warehouse.master_username
}

output "redshift_iam_role_arn" {
  description = "Role ARN to put in dwh.cfg as IAM_ROLE.ARN."
  value       = aws_iam_role.redshift_s3_read.arn
}

output "redshift_password_secret_arn" {
  description = "Secrets Manager ARN containing the Redshift admin credentials."
  value       = aws_redshift_cluster.warehouse.master_password_secret_arn
}
