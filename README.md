# Amazon Intelligence: Cloud-Native Real-Time Product Recommendation System

[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonwebservices&logoColor=white)](https://aws.amazon.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white)](https://kubernetes.io/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![Apache Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![MLflow](https://img.shields.io/badge/MLflow-0194E2?style=for-the-badge&logo=mlflow&logoColor=white)](https://mlflow.org/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=githubactions&logoColor=white)](https://github.com/features/actions)
[![Prometheus](https://img.shields.io/badge/Prometheus-E6522C?style=for-the-badge&logo=prometheus&logoColor=white)](https://prometheus.io/)

A high-performance, enterprise-grade Big Data pipeline designed for real-time product recommendations at scale. This system leverages the **Amazon Fine Food Reviews** dataset to deliver personalized experiences through a decoupled, cloud-native architecture on AWS EKS.

---

## 🚀 Project Overview & Business Value

In the modern e-commerce landscape, real-time personalization is a critical driver of user engagement and conversion. This system implements a complete end-to-end data lifecycle:
- **Streaming Ingestion:** Captures high-velocity user interaction events via **Apache Kafka**.
- **Batch Training:** Periodically trains an **ALS (Alternating Least Squares)** collaborative filtering model on **Apache Spark**, achieving a robust RMSE of ~0.90.
- **Real-Time Serving:** Delivers sub-30ms recommendations via a **FastAPI** backend, handling both known users and "Cold Start" scenarios with intelligent fallback logic.

The primary technical achievement is the migration from a monolithic Docker setup to a **Cloud-Native EKS architecture**, implementing strict MLOps principles, automated CI/CD, and full observability.

---

## 🏗️ Cloud-Native Architecture

The architecture is built on five distinct tiers, ensuring high availability and elastic scalability.

![Cloud Architecture](.docs/architecture.png)

### The 5 Tiers of Production:
1.  **Infrastructure (Terraform):** Fully automated provisioning of VPC, EKS, S3 Data Lake, and RDS PostgreSQL instances using Infrastructure as Code (IaC).
2.  **Orchestration (EKS/Airflow):** Apache Airflow running on **KubernetesExecutor**, enabling ephemeral pod execution for every task to maximize resource efficiency.
3.  **Data & MLOps (Spark/S3/MLflow):** Spark jobs running as `SparkApplication` CRDs. Models are tracked and versioned in the **MLflow Model Registry**, with artifacts stored securely in **Amazon S3**.
4.  **Serving (FastAPI/PostgreSQL):** A high-concurrency FastAPI layer serving personalized results stored in a high-performance PostgreSQL sink.
5.  **Observability (Prometheus/Grafana):** Full-stack monitoring with automated ServiceMonitors and pre-loaded Grafana dashboards for "Golden Signals" tracking.

---

## 🛠️ Airflow DAG & Orchestration

Orchestration is handled by a production-hardened Airflow DAG that utilizes the **KubernetesPodOperator** and **SparkKubernetesOperator**.

![Airflow DAG](.docs/airflow_dag_view.png)

By using the **Spark Operator**, we move away from traditional `spark-submit` to a cloud-native approach where Spark jobs are managed as native Kubernetes resources. This allows for:
- **Dynamic Resource Allocation:** Pods are only created when needed.
- **Improved Isolation:** Each task runs in its own dedicated, clean environment.
- **Native Kubernetes RBAC:** Leveraging ServiceAccounts and IRSA for secure access to AWS resources.

---

## 🌐 Serving & User Interface

The serving layer is designed for speed and reliability. The FastAPI backend is instrumented for production and provides a clean interface for recommendation retrieval.

![Dashboard UI](.docs/dashboard_ui.png)

- **FastAPI Backend:** Handles thousands of requests per second with asynchronous database pooling.
- **Cold Start Logic:** Automatically identifies new users and provides high-quality popular product fallbacks to ensure a seamless UX.
- **Internal Metrics:** Exposes a secure `/metrics` endpoint for Prometheus scraping.

---

## 🔄 CI/CD Pipeline (GitOps)

Our GitHub Actions workflow implements industry-standard DevOps practices for every push to the `main` branch:

1.  **Automated Linting:** Uses **Ruff** for high-speed Python static analysis.
2.  **Parallel Multi-Image Builds:** Simultaneously builds three custom Docker images (`API`, `Producer`, `Spark-ML`).
3.  **Immutable Tagging:** Every deployment is tagged with the **Git Commit SHA** and pushed to **Docker Hub**, ensuring 100% traceability and easy rollbacks.
4.  **Automated EKS Deployment:** Dynamically updates Kubernetes manifests using targeted `sed` replacements for registry and tag placeholders before executing `kubectl apply`.

---

## 📊 Observability Stack

We follow the "Everything as Code" philosophy for our monitoring stack:
- **FastAPI Instrumentation:** Automated via `prometheus-fastapi-instrumentator`.
- **Metrics Scraping:** Strictly internal to the cluster network via **ServiceMonitors**, ensuring zero public exposure of sensitive performance data.
- **Automated Dashboards:** Grafana dashboards are packaged as Kubernetes **ConfigMaps** with sidecar labels, allowing the monitoring stack to auto-discover and load them at launch.

---

## 🏁 Getting Started / Deployment Guide

To deploy this architecture to your AWS account:

1.  **Provision Infrastructure:**
    ```bash
    cd terraform/environments/dev
    terraform init && terraform apply
    ```
2.  **Configure Kubernetes:**
    ```bash
    aws eks update-kubeconfig --name <EKS_CLUSTER_NAME> --region <AWS_REGION>
    ```
3.  **Deploy Monitoring & Apps:**
    ```bash
    helm install prometheus prometheus-community/kube-prometheus-stack -f monitoring/values-monitoring.yaml
    kubectl apply -f k8s/ --recursive
    ```
4.  **Configure Secrets:**
    Ensure GitHub Secrets are set for `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN`, and AWS credentials to trigger the automated CI/CD pipeline.

---

© 2026 - Big Data & DevOps Project - [Yassine Kamouss](https://github.com/yassinekamouss)
