import os
from datetime import datetime
import logging
import json
import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.sql.functions import col
import pyspark.sql.functions as F
from pyspark.ml.feature import StringIndexer
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import ParamGridBuilder, TrainValidationSplit

# Logging Configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Environment Variables
S3_BUCKET = os.getenv("S3_DATA_LAKE_BUCKET", "amazon-recommender-datalake")
MLFLOW_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow-service.mlops.svc.cluster.local:5000")

# S3 Paths
DATA_PATH = f"s3a://{S3_BUCKET}/data/Reviews.csv"

def main():
    logger.info("Initializing MLflow tracking URI...")
    mlflow.set_tracking_uri(MLFLOW_URI)
    
    logger.info("Initializing SparkSession connected to the cluster...")
    spark = SparkSession.builder \
        .appName("ProductRecommendationTrainingAWS") \
        .master("spark://spark-master:7077") \
        .config("spark.executor.memory", "2g") \
        .config("spark.driver.memory", "1g") \
        .config("spark.executor.cores", "2") \
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "com.amazonaws.auth.DefaultAWSCredentialsProviderChain") \
        .config("mapreduce.fileoutputcommitter.marksuccessfuljobs", "false") \
        .config("mapreduce.fileoutputcommitter.algorithm.version", "2") \
        .config("spark.hadoop.mapreduce.fileoutputcommitter.algorithm.version", "2") \
        .config("spark.speculation", "false") \
        .getOrCreate()

    try:
        with mlflow.start_run():
            logger.info(f"Loading data from {DATA_PATH}...")
            df = spark.read.csv(DATA_PATH, header=True, inferSchema=True)
            
            df = df.withColumn("Time", col("Time").cast("long"))
            df = df.withColumn("Id", col("Id").cast("int"))

            df = df.select(
                df['UserId'].cast('string'),
                df['ProductId'].cast('string'),
                df['Score'].cast('float')
            )
            
            logger.info("Preprocessing: Removing null values and duplicates...")
            df = df.dropna(subset=['UserId', 'ProductId', 'Score'])
            df = df.dropDuplicates(['UserId', 'ProductId'])

            logger.info("Strict filtering: users (>= 5 reviews) and products (>= 5 ratings)...")
            user_counts = df.groupBy("UserId").count().filter(F.col("count") >= 5).select("UserId")
            df = df.join(user_counts, "UserId", "inner")
            
            item_counts = df.groupBy("ProductId").count().filter(F.col("count") >= 5).select("ProductId")
            df = df.join(item_counts, "ProductId", "inner")

            logger.info("Preprocessing: Transformation with StringIndexer...")
            df.cache()
            
            user_indexer = StringIndexer(inputCol="UserId", outputCol="user_index", handleInvalid="keep")
            item_indexer = StringIndexer(inputCol="ProductId", outputCol="item_index", handleInvalid="keep")

            user_indexer_model = user_indexer.fit(df)
            df = user_indexer_model.transform(df)

            item_indexer_model = item_indexer.fit(df)
            df = item_indexer_model.transform(df)

            logger.info("Data Split: 80% (Train+Validation), 20% (Test)...")
            (train_val_data, test_data) = df.randomSplit([0.8, 0.2], seed=42)

            als = ALS(
                userCol="user_index",
                itemCol="item_index",
                ratingCol="Score",
                coldStartStrategy="drop"
            )
                
            evaluator = RegressionEvaluator(
                metricName="rmse",
                labelCol="Score",
                predictionCol="prediction"
            )
            
            logger.info("Configuring hyperparameter grid...")
            param_grid = ParamGridBuilder() \
                .addGrid(als.rank, [10, 20]) \
                .addGrid(als.regParam, [0.1, 0.05]) \
                .build()

            tvs = TrainValidationSplit(
                estimator=als,
                estimatorParamMaps=param_grid,
                evaluator=evaluator,
                trainRatio=0.88 
            )

            logger.info("Training and validating ALS model...")
            tvs_model = tvs.fit(train_val_data)
            best_model = tvs_model.bestModel

            logger.info("Final model evaluation on the test set (20%)...")
            test_predictions = best_model.transform(test_data)
            final_rmse = evaluator.evaluate(test_predictions)
            logger.info(f"*** FINAL RMSE ON TEST SET = {final_rmse} ***")

            # --- MLflow Logging ---
            try:
                reg_param = best_model.getOrDefault(best_model.getParam("regParam"))
            except:
                reg_param = 0.1 

            mlflow.log_param("rank", best_model.rank)
            mlflow.log_param("regParam", reg_param)
            mlflow.log_metric("rmse", final_rmse)
            
            logger.info("Saving model and indexers to S3 and MLflow...")
            mlflow.spark.log_model(
                best_model, 
                "als_model", 
                registered_model_name="ProductRecommender"
            )
            
            user_indexer_model.write().overwrite().save(f"s3a://{S3_BUCKET}/models/user_indexer")
            item_indexer_model.write().overwrite().save(f"s3a://{S3_BUCKET}/models/item_indexer")

            logger.info("Training pipeline completed successfully.")
            
    except Exception as e:
        logger.error(f"Error encountered during training: {str(e)}")
        import sys
        sys.exit(1)
    finally:
        spark.stop()
        logger.info("SparkSession stopped.")

if __name__ == "__main__":
    main()