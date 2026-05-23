variable "region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "recommender-system"
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "dev"
}

variable "db_password" {
  description = "The database password"
  type        = string
  sensitive   = true
}
