from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, IntegerType, TimestampType
import logging

# Setting up logging for proper debugging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("KafkaToPostgres")

# Defining the expected schema of Kafka messages
schema = StructType() \
    .add("patient_id", IntegerType()) \
    .add("timestamp", TimestampType()) \
    .add("heart_rate", IntegerType())

# Initializing Spark session
spark = SparkSession.builder.appName("KafkaToPostgres").getOrCreate()

# Reading data from Kafka topic
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "heartbeat-topic") \
    .option("startingOffsets", "latest") \
    .load()

# Parsing Kafka messages and extracting JSON data
parsed_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .dropna()

# Writing data to PostgreSQL
def write_batch(batch_df, batch_id):
    try:
        batch_df.write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://postgres:5432/heartbeat_db") \
            .option("dbtable", "heartbeats") \
            .option("user", "postgres") \
            .option("password", "postgres") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()
        log.info(f"Batch {batch_id} written to PostgreSQL.")
    except Exception as e:
        log.error(f"Error writing batch {batch_id}: {e}")

# Starting the streaming query
parsed_df.writeStream \
    .foreachBatch(write_batch) \
    .option("checkpointLocation", "/tmp/spark_checkpoint") \    
    .start() \
    .awaitTermination()
 
   
# General comments about the code:
# Overall, this code reads data from a Kafka topic, parses it into JSON format, and writes it to a PostgreSQL database.
# The code uses a checkpoint location to ensure that the data is written to the database only once per batch.
