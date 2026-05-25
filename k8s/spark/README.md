# Spark on Kubernetes Installation

1. Add the Helm repo:
   helm repo add spark-operator https://googlecloudplatform.github.io/spark-on-k8s-operator

2. Install the operator:
   helm install my-release spark-operator/spark-operator --namespace default --set webhook.enable=true

3. Apply RBAC for Spark jobs:
   kubectl apply -f rbac.yaml
