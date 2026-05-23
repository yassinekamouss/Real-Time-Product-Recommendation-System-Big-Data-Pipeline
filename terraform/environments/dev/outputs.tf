output "vpc_id" {
  value = module.vpc.vpc_id
}

output "eks_cluster_name" {
  value = module.eks.cluster_name
}

output "eks_cluster_endpoint" {
  value = module.eks.cluster_endpoint
}

output "s3_bucket_name" {
  value = module.s3_data_lake.bucket_id
}

output "rds_endpoint" {
  value = module.rds.db_instance_endpoint
}
