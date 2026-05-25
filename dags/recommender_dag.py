import os
from datetime import datetime, timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.operators.bash import BashOperator
from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from airflow.providers.cncf.kubernetes.sensors.spark_kubernetes import SparkKubernetesSensor

# Configuration from environment or Airflow Variables (Templated to avoid DB hits at parse time)
S3_BUCKET = "{{ var.value.S3_DATA_LAKE_BUCKET }}"
MLFLOW_URI = "{{ var.value.MLFLOW_TRACKING_URI }}"

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
    description='Pipeline Cloud-Native: Ingestion & Apprentissage sur EKS',
    schedule_interval='@daily',
    start_date=datetime(2026, 4, 1),
    catchup=False,
    max_active_runs=1,
    tags=['kubernetes', 'spark', 'mlops', 'production'],
) as dag:

    # 1. Vérification de la disponibilité de Kafka
    wait_for_kafka = BashOperator(
        task_id='wait_for_kafka',
        bash_command='nc -z kafka 29092', # À ajuster selon le DNS interne si nécessaire
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
    sys.exit(1)
"'''
    )

    # ---------------------------------------------------------
    # BRANCHE 1 : LE FLUX DE DONNÉES (SIMULATION TEMPS RÉEL)
    # ---------------------------------------------------------
    ingest_data = KubernetesPodOperator(
        task_id='ingest_data_producer',
        name='kafka-producer',
        namespace='default',
        image='amazon-recommender-producer:latest',
        env_vars={
            'KAFKA_BROKER': "{{ var.value.kafka_broker_url }}",
        },
        get_logs=True,
        is_delete_operator_pod=True
    )

    # ---------------------------------------------------------
    # BRANCHE 2 : INTELLIGENCE ARTIFICIELLE & INFERENCE
    # ---------------------------------------------------------
    train_model = SparkKubernetesOperator(
        task_id='train_als_model',
        namespace='default',
        application_file='k8s/spark/train_job.yaml',
        do_xcom_push=True,
    )

    train_model_sensor = SparkKubernetesSensor(
        task_id='train_als_model_sensor',
        namespace='default',
        application_name="{{ task_instance.xcom_pull(task_ids='train_als_model')['metadata']['name'] }}",
        poke_interval=10,
    )

    start_streaming = SparkKubernetesOperator(
        task_id='start_realtime_streaming',
        namespace='default',
        application_file='k8s/spark/streaming_job.yaml',
        do_xcom_push=True,
    )

    # =========================================================
    # L'ORCHESTRATION PARALLÈLE
    # =========================================================
    
    check_mlflow = BashOperator(
        task_id='check_mlflow_health',
        bash_command="curl -fsSL " + MLFLOW_URI + "/health || (echo 'MLflow tracking server not reachable' && exit 1)",
    )

    # Pipeline
    wait_for_kafka >> create_kafka_topic
    create_kafka_topic >> ingest_data
    create_kafka_topic >> check_mlflow >> train_model >> train_model_sensor >> start_streaming
