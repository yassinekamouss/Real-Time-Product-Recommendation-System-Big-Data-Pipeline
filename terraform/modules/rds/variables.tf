variable "project_name" {
  description = "Project name for tagging"
  type        = string
}

variable "environment" {
  description = "Environment name for tagging"
  type        = string
}

variable "vpc_id" {
  description = "The ID of the VPC"
  type        = string
}

variable "private_subnet_ids" {
  description = "List of private subnet IDs"
  type        = list(string)
}

variable "db_name" {
  description = "The name of the database"
  type        = string
  default     = "airflow"
}

variable "db_user" {
  description = "The database user"
  type        = string
  default     = "airflow"
}

variable "db_password" {
  description = "The database password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "The instance class for the DB"
  type        = string
  default     = "db.t3.micro"
}

variable "allowed_security_group_ids" {
  description = "List of security group IDs allowed to connect to the DB"
  type        = list(string)
  default     = []
}
