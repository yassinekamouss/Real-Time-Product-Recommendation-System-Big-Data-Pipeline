# [PROJECT_NAME] : Real-Time Product Recommendation System Big Data Pipeline

[![Spark](https://img.shields.io/badge/Apache_Spark-E25A1C?style=for-the-badge&logo=apachespark&logoColor=white)](https://spark.apache.org/)
[![Kafka](https://img.shields.io/badge/Apache_Kafka-231F20?style=for-the-badge&logo=apachekafka&logoColor=white)](https://kafka.apache.org/)
[![Airflow](https://img.shields.io/badge/Apache_Airflow-017CEE?style=for-the-badge&logo=apacheairflow&logoColor=white)](https://airflow.apache.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![AWS](https://img.shields.io/badge/AWS-232F3E?style=for-the-badge&logo=amazonwebservices&logoColor=white)](https://aws.amazon.com/)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?style=for-the-badge&logo=terraform&logoColor=white)](https://www.terraform.io/)
[![MLflow](https://img.shields.io/badge/MLflow-0194E2?style=for-the-badge&logo=mlflow&logoColor=white)](https://mlflow.org/)

> **Status:** Production Ready - v2.0.0 (Cloud-Native)  
> **Objective:** Highly scalable Big Data architecture for real-time product recommendations, featuring automated MLOps, cloud-native storage, and infrastructure as code.

---

## 1. Introduction

This project implements a complete, real-time product recommendation engine using the *Amazon Fine Food Reviews* dataset. The architecture has been migrated to a **Cloud-Native AWS** stack to ensure high availability, scalability, and robust MLOps practices.

Key capabilities:
- **Scalable Ingestion:** Continuous user interaction streams via Apache Kafka (KRaft mode).
- **Distributed Training:** Spark ALS (Collaborative Filtering) on a standalone cluster.
- **MLOps Integration:** MLflow for experiment tracking and Model Registry for versioned model serving.
- **Cloud Storage:** S3-based Data Lake for datasets, model artifacts, and checkpoints.
- **Infrastructure as Code:** Fully automated provisioning via Terraform.

---

## 2. Architecture

The system follows a modern decoupled architecture, moving from local containers to a production-grade AWS environment.

- **Ingestion:** Kafka Broker (KRaft) receiving user events.
- **Compute:** Spark Master/Workers processing Batch (Training) and Streaming (Inference) jobs.
- **Storage:** 
    - **S3:** Data Lake for raw data (`Reviews.csv`), indexers, and Spark checkpoints.
    - **PostgreSQL (RDS/Container):** Serving layer for pre-computed recommendations.
- **Orchestration:** Apache Airflow managing the end-to-end lifecycle.
- **Serving:** FastAPI retrieving recommendations from Postgres and metrics from MLflow.

---

## 3. Tech Stack & MLOps

| Technology | Role | Cloud-Native Integration |
| :--- | :--- | :--- |
| **Apache Spark** | Processing Engine | S3A protocol for S3 data access. |
| **Apache Kafka** | Message Broker | KRaft mode for simplified orchestration. |
| **MLflow** | MLOps / Registry | Tracking experiments and model versioning. |
| **Terraform** | IaC | Modular AWS infrastructure (VPC, EKS, RDS, S3). |
| **PostgreSQL** | Sink / DB | RDS (Production) or Container (Dev). |
| **Apache Airflow** | Orchestrator | IRSA (IAM Roles for Service Accounts) for AWS access. |

---

## 4. Installation & Deployment

### Local Development (Docker)

1. **Clone & Setup:**
   ```bash
   git clone https://github.com/yassinekamouss/Real-Time-Product-Recommendation-System-Big-Data-Pipeline-.git
   cd Real-Time-Product-Recommendation-System-Big-Data-Pipeline-
   ```

2. **Download Dataset:**
   - Download `Reviews.csv` from [Kaggle](https://www.kaggle.com/datasets/snap/amazon-fine-food-reviews).
   - Place it in the `data/` directory.

3. **Launch:**
   ```bash
   docker compose up -d --build
   ```

### AWS Deployment (Terraform)

1. **Initialize Terraform:**
   ```bash
   cd terraform/environments/dev
   terraform init
   ```

2. **Deploy Infrastructure:**
   ```bash
   terraform apply -var="db_password=your_secure_password"
   ```

3. **Access Interfaces:**
   - **Airflow UI:** `http://localhost:8081` (Port forwarded)
   - **Spark UI:** `http://localhost:8080`
   - **API Dashboard:** `http://localhost:8000`
   - **MLflow UI:** `http://mlflow-service.mlops.svc.cluster.local:5000`

---

## 5. MLOps Workflow

1. **Training:** The Airflow DAG triggers `train_model.py`. Results (RMSE, parameters) are logged to MLflow, and the model is registered in the **Model Registry**.
2. **Registry Sync:** `streaming_recommender.py` periodically checks the MLflow Registry for new "Production" or "Latest" versions.
3. **Hot Swap:** The streaming job reloads the model from S3/MLflow *without restarting*, ensuring zero-downtime model updates.
4. **Monitoring:** The FastAPI dashboard fetches real-time performance metrics directly from the MLflow API.

---

## 6. Results & Performance

| Metric | Local Baseline | Cloud Optimized |
| :--- | :--- | :--- |
| **RMSE** | 2.38 | **0.90** |
| **Inference Latency** | ~1.2s / batch | **< 0.5s / batch** |
| **Serving Latency** | ~45ms | **~25ms (RDS)** |
| **Scalability** | Fixed (Docker) | **Elastic (EKS/Spark)** |

---

## 7. Project Team

- **[Yassine Kamouss]** - Architecture Big Data & DevOps
- **[Yahya Ahmane]** - Machine Learning & Data Engineering
- **[Mohammed Salhi]** - API Development & Orchestration MLOps (Airflow)

---

© 2026 - Big Data Project Report - Faculty of Science and Technology.

