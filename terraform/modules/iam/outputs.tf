output "cluster_role_arn" {
  description = "The ARN of the EKS cluster role"
  value       = aws_iam_role.cluster.arn
}

output "node_role_arn" {
  description = "The ARN of the EKS node role"
  value       = aws_iam_role.nodes.arn
}
