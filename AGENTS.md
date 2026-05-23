# Agent Guide: Real-Time Product Recommendation System

This file provides high-signal technical context for AI agents working on this repository.

## 🏗️ Architecture Summary
- **Orchestration:** Apache Airflow (`dags/recommender_dag.py`).
- **Processing:** Apache Spark (Standalone cluster).
- **Ingestion:** Apache Kafka (KRaft mode).
- **Storage:** PostgreSQL (Shared between Airflow and FastAPI).
- **Serving:** FastAPI (`src/dashboard/`).

## 🌐 Networking & Connections
Always use internal Docker DNS names when running code within the containerized environment:
- **Kafka Broker:** `kafka:29092`
- **Spark Master:** `spark://spark-master:7077`
- **PostgreSQL:** `postgres:5432` (DB: `airflow`, User: `airflow`)
- **FastAPI API:** `http://localhost:8000` (from host) or `api-recommendation:8000` (internal)

## 📂 Path Mapping Matrix
The project root is mounted to different absolute paths depending on the container. Resolve paths accordingly:

| Component | Host Path | Container Path |
| :--- | :--- | :--- |
| **Airflow** | `./` | `/opt/airflow/` |
| **Spark** | `./` | `/opt/spark/` |
| **Models** | `./models/` | `/opt/spark/models/` |
| **Data** | `./data/` | `/opt/spark/data/` |

**Crucial:** Spark jobs usually read/write to `/opt/spark/models/` or `/opt/spark/data/`.

## ⚡ Critical Development Facts
- **Spark Dependencies:** Streaming jobs MUST include:
  `--packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1`
- **ML Algorithm:** ALS (Collaborative Filtering).
- **Cold Start:** Use `coldStartStrategy="drop"` in ALS to avoid NaN errors.
- **Data Prerequisite:** `data/Reviews.csv` must be manually downloaded to the `data/` directory (not in Git).
- **Entry Point:** The primary workflow is the Airflow DAG `amazon_recommender_pipeline` found in `dags/recommender_dag.py`.

## 🛠️ Common Commands
- **Start System:** `docker compose up -d`
- **Logs:** `docker compose logs -f [service_name]`
- **Spark Submit (via Airflow):** Check `dags/recommender_dag.py` for exact `SparkSubmitOperator` configurations.
