# Design Spec: AWS S3 & MLflow MLOps Migration

## Overview
Migration of the Real-Time Product Recommendation System from local storage to a cloud-native architecture using AWS S3 for data/checkpoints and MLflow for model management (Tracking & Registry).

## Goals
- Decouple application code from infrastructure using environment variables.
- Implement a robust MLOps lifecycle with MLflow Model Registry.
- Enable S3 connectivity in Spark using the `s3a://` protocol.
- Securely handle AWS authentication via IAM Roles for Service Accounts (IRSA).

## Architecture

### Data Storage (S3)
- **Input Data:** `s3a://${S3_DATA_LAKE_BUCKET}/data/Reviews.csv`
- **Spark Checkpoints:** `s3a://${S3_DATA_LAKE_BUCKET}/checkpoints/streaming/`
- **Artifacts:** Managed by MLflow, stored in the S3 bucket's artifact root.

### MLOps Pipeline (MLflow)
- **Tracking Server:** Self-hosted on EKS at `http://mlflow-service.mlops.svc.cluster.local:5000`.
- **Backend Store:** AWS RDS PostgreSQL.
- **Model Registry:** Models are registered as `ProductRecommender`.

## Component Details

### 1. Spark Training (`train_model.py`)
- **Integration:** Uses `mlflow` Python library.
- **Run Management:** All training logic wrapped in `mlflow.start_run()`.
- **Metrics:** Logs `rmse`, `rank`, and `regParam`.
- **Registration:** Logs the Spark model and registers it to the Model Registry.
- **Refactoring:** Removal of local `archive` and `file://` based logic.

### 2. Streaming Inference (`streaming_recommender.py`)
- **Model Loading:** Fetches the model directly from MLflow using `models:/ProductRecommender/latest`.
- **Indexers:** Loaded from S3 paths derived from environment variables.
- **Checkpoints:** Stored in S3.

### 3. Environment & Spark Configuration
- **S3 Connectivity:** Use `hadoop-aws` and `aws-java-sdk-bundle` JARs.
- **Authentication:** Use `com.amazonaws.auth.DefaultAWSCredentialsProviderChain`.
- **Environment Variables:**
  - `S3_DATA_LAKE_BUCKET`
  - `MLFLOW_TRACKING_URI`

### 4. Containerization (`Dockerfile.spark`)
- Install `mlflow`, `boto3`, `psycopg2-binary`.
- Manually download/copy AWS JARs to `$SPARK_HOME/jars/` to avoid dependency resolution issues at runtime.

## Success Criteria
- Training script successfully logs to MLflow and registers a model.
- Streaming script successfully pulls the `latest` model from the registry.
- No hardcoded paths or credentials in the source code.
- Spark can read/write to S3 using IRSA permissions.
