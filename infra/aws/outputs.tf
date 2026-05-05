output "vpc_id" {
  description = "ID of the VPC the deployment lives in."
  value       = aws_vpc.this.id
}

output "db_endpoint" {
  description = "RDS Postgres endpoint (host:port)."
  value       = aws_db_instance.postgres.endpoint
  sensitive   = true
}

output "frontend_bucket" {
  description = "S3 bucket holding the built web bundle."
  value       = aws_s3_bucket.frontend.bucket
}
