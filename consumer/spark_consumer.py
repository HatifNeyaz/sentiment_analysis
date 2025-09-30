# consumer.py

import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, udf
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, IntegerType
import joblib

KAFKA_TOPIC = "twitter-stream"
KAFKA_SERVER = "kafka:9092"
MONGO_URI = "mongodb://root:password@mongo:27017/"
MONGO_DB = "sentiment_db"
MONGO_COLLECTION = "tweets"
# FIX: Use an absolute path starting with "/"
MODEL_PATH = "/app/models/sentiment_pipeline.joblib"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_spark_session():
    try:
        spark = SparkSession.builder \
            .appName("SentimentAnalysisStreamToMongo") \
            .getOrCreate()
        spark.sparkContext.setLogLevel("ERROR")
        logging.info("SparkSession created successfully.")
        return spark
    except Exception as e:
        logging.error(f"Error creating SparkSession: {e}")
        raise

def load_model(path):
    try:
        model = joblib.load(path)
        logging.info(f"Model loaded successfully from {path}")
        return model
    except FileNotFoundError:
        logging.error(f"Model file not found at {path}.")
        raise

def create_sentiment_udf(spark, model_path):
    broadcasted_model = spark.sparkContext.broadcast(load_model(model_path))
    def predict_sentiment(text):
        if text is None: return None
        prediction = broadcasted_model.value.predict([text])
        return int(prediction[0])
    return udf(predict_sentiment, IntegerType())

def write_batch_to_mongo(df, epoch_id):
    if df.count() > 0:
        logging.info(f"Writing batch {epoch_id} to MongoDB...")
        df.write.format("mongodb") \
            .mode("append") \
            .option("connection.uri", MONGO_URI) \
            .option("database", MONGO_DB) \
            .option("collection", MONGO_COLLECTION) \
            .option("authSource", "admin") \
            .save()
        logging.info(f"Batch {epoch_id} successfully written to MongoDB.")

def process_stream(spark, sentiment_udf):
    DATA_SCHEMA = StructType([
        StructField("id", LongType(), True),
        StructField("text", StringType(), True),
        StructField("timestamp", DoubleType(), True)
    ])
    kafka_df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", KAFKA_SERVER) \
        .option("subscribe", KAFKA_TOPIC) \
        .load()
    json_df = kafka_df.selectExpr("CAST(value AS STRING) as json_string") \
        .select(from_json(col("json_string"), DATA_SCHEMA).alias("data")) \
        .select("data.*")
    prediction_df = json_df.withColumn("sentiment", sentiment_udf(col("text")))
    mongo_query = prediction_df.writeStream \
        .foreachBatch(write_batch_to_mongo) \
        .outputMode("append") \
        .trigger(processingTime='10 seconds') \
        .start()
    logging.info("Streaming query to MongoDB started...")
    mongo_query.awaitTermination()

def main():
    spark = create_spark_session()
    sentiment_udf = create_sentiment_udf(spark, MODEL_PATH)
    process_stream(spark, sentiment_udf)

if __name__ == "__main__":
    main()