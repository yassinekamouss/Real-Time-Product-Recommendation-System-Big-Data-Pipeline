terraform {
  # Note: The S3 bucket and DynamoDB table must be created manually or via a separate 'bootstrap' stack first.
  # backend "s3" {
  #   bucket         = "my-terraform-state-bucket"
  #   key            = "dev/recommender-system.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-lock-table"
  # }

  required_version = "~> 1.7"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
