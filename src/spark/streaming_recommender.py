import os
import json
import logging
import psycopg2
import time
from psycopg2.extras import execute_values
import mlflow.spark
from mlflow.tracking import MlflowClient
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, FloatType, LongType
from pyspark.ml.recommendation import ALSModel
from pyspark.ml.feature import StringIndexerModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "airflow")
DB_USER = os.getenv("POSTGRES_USER", "airflow")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "airflow_pass")

KAFKA_BROKER = os.getenv("KAFKA_BROKER", "kafka:29092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "user-ratings")

SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://spark-master:7077")

S3_BUCKET = os.getenv("S3_DATA_LAKE_BUCKET", "amazon-recommender-datalake")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlops.svc.cluster.local:5000")
CHECKPOINT_DIR = f"s3a://{S3_BUCKET}/checkpoints/streaming"
USER_INDEXER_PATH = f"s3a://{S3_BUCKET}/models/user_indexer"
ITEM_INDEXER_PATH = f"s3a://{S3_BUCKET}/models/item_indexer"

TOP_N = int(os.getenv("RECOMMEND_TOP_N", "5"))

def init_db():
    """
    Initialize the table upon startup.
    This ensures the API never crashes, even if Kafka is empty.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS user_recommendations (
                "UserId" VARCHAR(255) PRIMARY KEY,
                recommendations TEXT
            )
        """)
        conn.commit()
        cur.close()
        logger.info("PostgreSQL table 'user_recommendations' successfully verified/created.")
    except Exception as e:
        logger.error(f"Error during table creation: {e}")
    finally:
        if conn:
            conn.close()

def save_to_postgres(batch_df, batch_id, item_labels_bc):
    """
    Saves the recommendations to PostgreSQL using foreachPartition to avoid OOM on the driver.
    """
    def save_partition(partition):
        conn = None
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
            )
            cur = conn.cursor()
            data = []
            labels = item_labels_bc.value
            
            for row in partition:
                user_id = str(row["UserId"])
                recs = []
                for rec in row["recommendations"]:
                    item_index = int(rec.item_index)
                    if 0 <= item_index < len(labels):
                        recs.append({
                            "ProductId": labels[item_index],
                            "score": float(rec.rating)
                        })
                data.append((user_id, json.dumps(recs)))

            if data:
                execute_values(cur, """
                    INSERT INTO user_recommendations ("UserId", recommendations)
                    VALUES %s
                    ON CONFLICT ("UserId") DO UPDATE
                    SET recommendations = EXCLUDED.recommendations;
                """, data)
                conn.commit()
            cur.close()
        except Exception as e:
            # Note: logging within partitions requires care; using print for simplicity in executors
            print(f"PostgreSQL insertion error in partition: {e}")
        finally:
            if conn:
                conn.close()

    # Apply the partition-level saving
    batch_df.foreachPartition(save_partition)
    logger.info(f"Batch {batch_id}: Recommendations update completed via foreachPartition.")

# Global state for models and indices
als_model = None
user_indexer = None
item_indexer = None
item_labels_bc = None
max_user_index = None
last_model_update = 0
current_model_version = None

def load_or_refresh_models(spark, force=False):
    """
    Checks for a newer model in the MLflow Model Registry and reloads if necessary.
    """
    global als_model, user_indexer, item_indexer, item_labels_bc, max_user_index, last_model_update, current_model_version
    
    now = time.time()
    # Check every hour (3600 seconds) unless forced
    if not force and (now - last_model_update < 3600):
        return False

    try:
        client = MlflowClient()
        # Look for the latest version in any of the standard stages
        latest_version_info = client.get_latest_versions("ProductRecommender", stages=["None", "Staging", "Production"])
        if not latest_version_info:
            if force: raise Exception("No model versions found in registry")
            return False
            
        latest_version = latest_version_info[0].version
        
        # Only reload if it's a new version or we are forcing it
        if not force and latest_version == current_model_version:
            last_model_update = now 
            return False

        logger.info(f"Updating models: Found version {latest_version} (Current: {current_model_version})")
        
        # Load new model and indexers
        new_als_model = mlflow.spark.load_model(f"models:/ProductRecommender/{latest_version}")
        new_user_indexer = StringIndexerModel.load(USER_INDEXER_PATH)
        new_item_indexer = StringIndexerModel.load(ITEM_INDEXER_PATH)
        
        # Update labels broadcast
        if item_labels_bc:
            item_labels_bc.unpersist()
        new_item_labels_bc = spark.sparkContext.broadcast(new_item_indexer.labels)
        
        try:
            new_max_user_index = new_als_model.userFactors.agg(F.max("id")).collect()[0][0]
        except Exception:
            new_max_user_index = None
            
        # Swap old for new
        als_model = new_als_model
        user_indexer = new_user_indexer
        item_indexer = new_item_indexer
        item_labels_bc = new_item_labels_bc
        max_user_index = new_max_user_index
        current_model_version = latest_version
        last_model_update = now
        
        logger.info(f"Model version {latest_version} successfully loaded and activated.")
        return True
    except Exception as e:
        logger.error(f"Failed to load or refresh models: {e}")
        if force: raise e
        return False

def main():
    # Initialize the table before launching Spark
    init_db()

    mlflow.set_tracking_uri(MLFLOW_URI)

    spark = SparkSession.builder \
        .appName("RealTimeRecommenderAWS") \
        .master(SPARK_MASTER) \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    try:
        load_or_refresh_models(spark, force=True)
    except Exception as e:
        logger.error(f"Initial model load failed: {e}")
        import sys; sys.exit(1)

    schema = StructType([
        StructField("UserId", StringType(), True),
        StructField("ProductId", StringType(), True),
        StructField("Score", FloatType(), True),
        StructField("Time", LongType(), True)
    ])

    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_BROKER) \
        .option("subscribe", KAFKA_TOPIC) \
        .option("startingOffsets", "earliest") \
        .option("maxOffsetsPerTrigger", 5000) \
        .option("failOnDataLoss", "false") \
        .load()

    parsed_df = kafka_df.selectExpr("CAST(value AS STRING) AS value") \
        .select(F.from_json(F.col("value"), schema).alias("data")) \
        .select("data.*") \
        .filter(F.col("UserId").isNotNull())

    def process_micro_batch(batch_df, batch_id):
        logger.info(f"========== MICRO BATCH {batch_id} RECEIVED ==========")

        # Periodically check for model updates
        load_or_refresh_models(spark)

        if batch_df.rdd.isEmpty():
            return

        unique_users = batch_df.select("UserId").distinct()

        # Transformation via model
        try:
            indexed_users = user_indexer.transform(unique_users).select("UserId", "user_index")
            indexed_users = indexed_users.filter(F.col("user_index").isNotNull())

            if max_user_index is not None:
                indexed_users = indexed_users.filter(F.col("user_index") <= F.lit(max_user_index))

            if indexed_users.rdd.isEmpty():
                logger.info("-> No users could be processed. Skipping insertion.")
                return

            recommendations = als_model.recommendForUserSubset(indexed_users, TOP_N)
            final_recs = recommendations.join(indexed_users, "user_index") \
                .select("UserId", "recommendations")

            save_to_postgres(final_recs, batch_id, item_labels_bc)
            
        except Exception as e:
            logger.error(f"FATAL ERROR DURING MICRO-BATCH: {e}")

    query = parsed_df.writeStream \
        .foreachBatch(process_micro_batch) \
        .option("checkpointLocation", CHECKPOINT_DIR) \
        .trigger(processingTime="120 seconds") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()