# AWS S3 & MLflow MLOps Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate Spark training and inference to AWS S3 and MLflow Model Registry, removing local dependencies and hardcoded infrastructure.

**Architecture:** Cloud-native Spark setup using `s3a://` for storage and MLflow for lifecycle management. Decoupled configuration via environment variables.

**Tech Stack:** PySpark 3.5.1, MLflow, Boto3, Hadoop-AWS, AWS Java SDK Bundle.

---

### Task 1: Update Dockerfile for S3 and MLflow Support

**Files:**
- Modify: `Dockerfile.spark`

- [ ] **Step 1: Update Dockerfile to include dependencies and JARs**

```dockerfile
FROM apache/spark:3.5.1

# On passe en root
USER root

# Installation des librairies pour S3 et MLflow
RUN pip install --no-cache-dir psycopg2-binary numpy pandas mlflow boto3

# Téléchargement des JARs AWS (Hadoop-AWS et AWS SDK Bundle)
# Note: Versions match Spark 3.5.1 (Hadoop 3.3.4)
RUN curl -o /opt/spark/jars/hadoop-aws-3.3.4.jar https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar && \
    curl -o /opt/spark/jars/aws-java-sdk-bundle-1.12.262.jar https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.262/aws-java-sdk-bundle-1.12.262.jar

USER spark
```

- [ ] **Step 2: Commit changes**

```bash
git add Dockerfile.spark
git commit -m "infra: add MLflow and AWS S3 dependencies to Spark Dockerfile"
```

---

### Task 2: Refactor `train_model.py` for S3 and MLflow

**Files:**
- Modify: `src/spark/train_model.py`

- [ ] **Step 1: Implement S3 paths and MLflow logging**

```python
import os
import logging
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
# ... existing imports ...

# Environment Variables
S3_BUCKET = os.getenv("S3_DATA_LAKE_BUCKET")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlops.svc.cluster.local:5000")

# S3 Paths
DATA_PATH = f"s3a://{S3_BUCKET}/data/Reviews.csv"
INDEXER_BASE_PATH = f"s3a://{S3_BUCKET}/models/indexers"

def main():
    mlflow.set_tracking_uri(MLFLOW_URI)
    
    spark = SparkSession.builder \
        .appName("ProductRecommendationTrainingAWS") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .getOrCreate()

    with mlflow.start_run():
        # ... logic to load data and train ...
        
        # Log metrics
        mlflow.log_param("rank", best_model.rank)
        mlflow.log_metric("rmse", final_rmse)
        
        # Register Model
        mlflow.spark.log_model(
            best_model, 
            "als_model", 
            registered_model_name="ProductRecommender"
        )
        
        # Save indexers to S3
        user_indexer_model.write().overwrite().save(f"{INDEXER_BASE_PATH}/user")
        item_indexer_model.write().overwrite().save(f"{INDEXER_BASE_PATH}/item")
```

- [ ] **Step 2: Commit changes**

```bash
git add src/spark/train_model.py
git commit -m "feat: migrate training script to S3 and MLflow"
```

---

### Task 3: Refactor `streaming_recommender.py` for S3 and MLflow Registry

**Files:**
- Modify: `src/spark/streaming_recommender.py`

- [ ] **Step 1: Implement Model Registry loading and S3 checkpoints**

```python
import os
import mlflow.spark
from pyspark.sql import SparkSession
# ... existing imports ...

S3_BUCKET = os.getenv("S3_DATA_LAKE_BUCKET")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlops.svc.cluster.local:5000")
CHECKPOINT_DIR = f"s3a://{S3_BUCKET}/checkpoints/streaming"
INDEXER_BASE_PATH = f"s3a://{S3_BUCKET}/models/indexers"

def main():
    mlflow.set_tracking_uri(MLFLOW_URI)
    
    spark = SparkSession.builder \
        .appName("RealTimeRecommenderAWS") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .getOrCreate()

    # Load from Registry
    als_model = mlflow.spark.load_model("models:/ProductRecommender/latest")
    
    # Load Indexers from S3
    user_indexer = StringIndexerModel.load(f"{INDEXER_BASE_PATH}/user")
    item_indexer = StringIndexerModel.load(f"{INDEXER_BASE_PATH}/item")
```

- [ ] **Step 2: Commit changes**

```bash
git add src/spark/streaming_recommender.py
git commit -m "feat: update streaming recommender to use MLflow registry and S3"
```
