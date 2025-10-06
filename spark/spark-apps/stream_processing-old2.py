from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, when, regexp_extract, to_timestamp, window
from pyspark.sql.types import StructType, StructField, StringType
from datetime import datetime
import os

# --- Spark Session Initialization ---
spark = SparkSession.builder \
    .appName("RealTimeIncidentProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")

print("Spark Session Created for IT Incident Processing. Reading from Kafka...")

# --- Configuration ---
KAFKA_BROKER_URL = 'kafka1:29092'
KAFKA_TOPIC_NAME = 'incidents'
OUTPUT_PATH_ENRICHED = "/opt/spark-data/data/enriched_incidents_hourly"
CHECKPOINT_PATH_ENRICHED = "/opt/spark-data/spark_checkpoints/enriched_incidents_checkpoint"
CHECKPOINT_PATH_ALERTS = "/opt/spark-data/spark_checkpoints/alerts_checkpoint"

# --- Schema Definition for Kafka Messages ---
# This schema must match the JSON structure being sent to Kafka.
LOG_EVENT_SCHEMA = StructType([
    StructField("timestamp", StringType(), True),
    StructField("level", StringType(), True),
    StructField("message", StringType(), True)
])

# --- Read from Kafka ---
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER_URL) \
    .option("subscribe", KAFKA_TOPIC_NAME) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# --- CORRECTED Base Processing: Use native from_json function ---
# This is the main correction. We remove the Python UDF and use Spark's built-in
# function for parsing JSON, which is much more efficient and reliable.
base_df = kafka_df.select(
    # 1. Cast the binary 'value' from Kafka into a readable string.
    # 2. Use from_json to parse the string using our defined schema.
    from_json(col("value").cast("string"), LOG_EVENT_SCHEMA).alias("data")
).select(
    # 3. Select the fields from the parsed data structure.
    to_timestamp(col("data.timestamp")).alias("event_time"),
    col("data.level").alias("level"),
    col("data.message").alias("message")
).withWatermark("event_time", "10 seconds")


# --- Enrichment Logic for IT Incidents ---
enriched_df = base_df.withColumn(
    "incident_id", regexp_extract(col("message"), r"(INC-\w+)", 1)
).withColumn(
    "service", regexp_extract(col("message"), r"Service: (\S+?)(?:[.,]|$)", 1)
).withColumn(
    "category", regexp_extract(col("message"), r"Category: ([\w\s]+?)(?:[.,]|$)", 1)
)

# After enrichment, replace any empty strings from failed regex matches with null.
enriched_df = enriched_df.withColumn("incident_id", when(col("incident_id") == "", None).otherwise(col("incident_id")))
enriched_df = enriched_df.withColumn("service", when(col("service") == "", None).otherwise(col("service")))
enriched_df = enriched_df.withColumn("category", when(col("category") == "", None).otherwise(col("category")))

# --- Aggregation for Incident Alerting ---
aggregated_df = enriched_df \
    .groupBy(
        window(col("event_time"), "5 minutes"),
        col("level")
    ).count()


# --- Alerting Logic for High-Severity Incidents ---
def process_alerts_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    print(f"--- Processing Alerts Batch {batch_id} ---")
    
    pandas_df = batch_df.select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("level"),
        col("count")
    ).toPandas()

    if pandas_df.empty:
        return

    for row in pandas_df.itertuples():
        if row.level == "ERROR" and row.count >= 3:
            alert_message = f"ALERT: High number of critical incidents! {row.count} ERRORs detected between {row.window_start} and {row.window_end}."
            print(f"\n\033[91m{alert_message}\033[0m\n")

# --- Function to Write Enriched Incident Data to Hourly Files ---
def write_enriched_to_hourly_csv(batch_df, batch_id):
    if batch_df.isEmpty(): return

    hourly_file_suffix = datetime.now().strftime("%Y-%m-%d_%H")
    output_file_path = os.path.join(OUTPUT_PATH_ENRICHED, f"incidents_{hourly_file_suffix}.csv")
    
    print(f"Batch {batch_id}: Writing {batch_df.count()} enriched incident rows to {output_file_path}")

    # Explicitly select and order columns for the output CSV
    output_df = batch_df.select("event_time", "level", "message", "incident_id", "service", "category")
    
    pandas_df = output_df.coalesce(1).toPandas()

    # Append to the hourly file, writing the header only if the file is new
    file_exists = os.path.exists(output_file_path)
    pandas_df.to_csv(output_file_path, mode='a', header=not file_exists, index=False)


# --- Start the Streaming Queries ---
enriched_query = enriched_df.writeStream \
    .foreachBatch(write_enriched_to_hourly_csv) \
    .outputMode("append") \
    .trigger(processingTime='1 minute') \
    .option("checkpointLocation", CHECKPOINT_PATH_ENRICHED) \
    .start()

alerting_query = aggregated_df.writeStream \
    .foreachBatch(process_alerts_batch) \
    .outputMode("update") \
    .trigger(processingTime='1 minute') \
    .option("checkpointLocation", CHECKPOINT_PATH_ALERTS) \
    .start()

print("Streaming queries for IT Incidents started. Waiting for termination...")
spark.streams.awaitAnyTermination()