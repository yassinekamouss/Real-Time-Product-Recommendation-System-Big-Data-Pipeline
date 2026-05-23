import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator

# Configuration from environment or Airflow Variables
S3_BUCKET = Variable.get("S3_DATA_LAKE_BUCKET", default_var=os.getenv("S3_DATA_LAKE_BUCKET", "recommender-system-data-lake-dev"))
MLFLOW_URI = Variable.get("MLFLOW_TRACKING_URI", default_var=os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlops.svc.cluster.local:5000"))

default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 2, # Un peu plus de résilience
    'retry_delay': timedelta(minutes=1),
}

with DAG(
    'amazon_recommender_pipeline',
    default_args=default_args,
    description='Pipeline Parallèle: Ingestion Temps Réel & Apprentissage ALS',
    schedule_interval='@daily',
    start_date=datetime(2026, 4, 1),
    catchup=False,
    tags=['spark', 'machine-learning', 'streaming', 'production'],
) as dag:

    # 1. Vérification de la disponibilité de Kafka
    wait_for_kafka = BashOperator(
        task_id='wait_for_kafka',
        bash_command='nc -z kafka 29092',
        retries=5,
        retry_delay=timedelta(seconds=15)
    )

    create_kafka_topic = BashOperator(
        task_id='create_kafka_topic',
        bash_command='''python -c "
import sys
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError

try:
    admin = KafkaAdminClient(bootstrap_servers='kafka:29092')
    admin.create_topics([NewTopic(name='user-ratings', num_partitions=1, replication_factor=1)])
    print('Topic créé avec succès')
except TopicAlreadyExistsError:
    print('Le Topic existe déjà.')
except Exception as e:
    print('Erreur fatale de création du topic:', e)
    sys.exit(1) # <-- INDISPENSABLE pour qu'Airflow détecte l'échec
"'''
    )

    # ---------------------------------------------------------
    # BRANCHE 1 : LE FLUX DE DONNÉES (SIMULATION TEMPS RÉEL)
    # ---------------------------------------------------------
    ingest_data = BashOperator(
        task_id='ingest_data_producer',
        bash_command='python /opt/airflow/src/producer/kafka_producer.py',
    )

    # ---------------------------------------------------------
    # BRANCHE 2 : INTELLIGENCE ARTIFICIELLE & INFERENCE
    # ---------------------------------------------------------
    # Soumission au cluster Spark (et non en local)
    train_model = SparkSubmitOperator(
        task_id='train_als_model',
        conn_id='spark_default', 
        application='/opt/airflow/src/spark/train_model.py',
        name='Batch_Training_ALS',
        # SUPPRESSION DU MASTER='local[*]' POUR UTILISER LA CONN_ID OU CONF
        conf={
            'spark.master': 'spark://spark-master:7077', # Force l'utilisation du cluster Docker
            'spark.driver.memory': '1g',
            'spark.executor.memory': '2g', # Aligné avec ton docker-compose
            'spark.executor.cores': '2'
        },
        env_vars={
            "S3_DATA_LAKE_BUCKET": S3_BUCKET,
            "MLFLOW_TRACKING_URI": MLFLOW_URI
        },
        verbose=True
    )

    start_streaming = SparkSubmitOperator(
        task_id='start_realtime_streaming',
        conn_id='spark_default',
        application='/opt/airflow/src/spark/streaming_recommender.py',
        # Packages nécessaires pour lire Kafka depuis Spark Structured Streaming
        packages='org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.1',
        name='Streaming_Inference',
        conf={
            'spark.master': 'spark://spark-master:7077',
            'spark.driver.memory': '1g',
            'spark.executor.memory': '2g',
        },
        env_vars={
            "S3_DATA_LAKE_BUCKET": S3_BUCKET,
            "MLFLOW_TRACKING_URI": MLFLOW_URI
        },
        verbose=True
    )

    # =========================================================
    # L'ORCHESTRATION PARALLÈLE (LE SECRET D'UN BON DAG)
    # =========================================================
    
    check_mlflow = BashOperator(
        task_id='check_mlflow_health',
        bash_command=f"curl -f {MLFLOW_URI}/health || echo 'MLflow tracking server not reachable' && exit 1",
    )

    # Nouveau pipeline
    wait_for_kafka >> create_kafka_topic
    create_kafka_topic >> ingest_data
    create_kafka_topic >> train_model >> check_mlflow >> start_streaming