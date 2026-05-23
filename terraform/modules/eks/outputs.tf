output "cluster_endpoint" {
  description = "The endpoint of the EKS cluster"
  value       = aws_eks_cluster.this.endpoint
}

output "cluster_name" {
  description = "The name of the EKS cluster"
  value       = aws_eks_cluster.this.name
}

output "cluster_certificate_authority_data" {
  description = "The CA data for the EKS cluster"
  value       = aws_eks_cluster.this.certificate_authority[0].data
}
