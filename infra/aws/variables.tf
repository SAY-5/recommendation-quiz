variable "region" {
  description = "AWS region to deploy into."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment tag (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "api_image" {
  description = "Fully qualified ECR image URI for the API container."
  type        = string
  default     = "REPLACE_ME.dkr.ecr.us-east-1.amazonaws.com/recommendation-quiz-api:latest"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC."
  type        = string
  default     = "10.42.0.0/16"
}

variable "db_username" {
  description = "Master username for RDS."
  type        = string
  default     = "quiz"
}

variable "db_password_ssm_arn" {
  description = "SSM parameter ARN holding the RDS master password (SecureString)."
  type        = string
  default     = ""
}

variable "frontend_bucket_name" {
  description = "S3 bucket that hosts the built web bundle."
  type        = string
  default     = "recommendation-quiz-web-REPLACE_ME"
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default = {
    project = "recommendation-quiz"
  }
}
