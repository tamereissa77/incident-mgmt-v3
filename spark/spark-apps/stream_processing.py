# Make sure you are editing the file that your Airflow DAG or spark-submit command is pointing to.
# The correct path in your project structure is likely:
# D:\vscodes\incedent mgmt - draft\Logs-Real-Time-Processing\spark\spark-apps\stream_processor.py

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, udf, from_json, expr, when, lit, regexp_extract, to_timestamp, window
from pyspark.sql.types import StructType, StructField, StringType
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.json_schema import JSONDeserializer
from confluent_kafka.serialization import SerializationContext
from datetime import datetime
import os

# --- Spark Session Initialization ---
spark = SparkSession.builder \
    .appName("RealTimeIncidentProcessor") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("WARN")  # Reduce verbosity

print("Spark Session Created for IT Incident Processing. Reading from Kafka...")

# --- Configuration ---
KAFKA_BROKER_URL = 'kafka1:29092'
KAFKA_TOPIC_NAME = 'incidents'  # Correctly set to the incidents topic
SCHEMA_REGISTRY_URL = "http://schema-registry:8081"

# --- Output Paths & Checkpoints ---
OUTPUT_PATH_ENRICHED = "/opt/spark-data/data/enriched_incidents_hourly"
CHECKPOINT_PATH_ENRICHED = "/opt/spark-data/spark_checkpoints/enriched_incidents_checkpoint"
CHECKPOINT_PATH_ALERTS = "/opt/spark-data/spark_checkpoints/alerts_checkpoint"

# Create output directories if they don't exist
os.makedirs(OUTPUT_PATH_ENRICHED, exist_ok=True)
os.makedirs(CHECKPOINT_PATH_ENRICHED, exist_ok=True)
os.makedirs(CHECKPOINT_PATH_ALERTS, exist_ok=True)

# --- Schema Definition for Kafka Messages ---
# This schema matches the JSON structure produced by your log_generator.py
LOG_EVENT_SCHEMA = StructType([
    StructField("timestamp", StringType(), True),
    StructField("level", StringType(), True),
    StructField("message", StringType(), True)
])

# --- Kafka Deserialization Logic (Kept from your original code) ---
# This is a robust way to handle Schema Registry and is kept as is.
_schema_registry_client = None
_json_deserializer = None

def get_json_deserializer():
    global _schema_registry_client, _json_deserializer
    if _json_deserializer is None:
        if _schema_registry_client is None:
            sr_config = {'url': SCHEMA_REGISTRY_URL}
            _schema_registry_client = SchemaRegistryClient(sr_config)
        _json_deserializer = JSONDeserializer(schema_str=None, schema_registry_client=_schema_registry_client, from_dict=lambda data, ctx: data)
    return _json_deserializer

def deserialize_json_value(value_bytes, topic_name):
    if value_bytes is None: return None
    try:
        deserializer = get_json_deserializer()
        context = SerializationContext(topic_name, 'value')
        return deserializer(value_bytes, context)
    except Exception as e:
        print(f"Error deserializing JSON Schema message: {e}")
        return None

deserialize_json_udf = udf(deserialize_json_value, LOG_EVENT_SCHEMA)

# --- Read from Kafka ---
kafka_df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", KAFKA_BROKER_URL) \
    .option("subscribe", KAFKA_TOPIC_NAME) \
    .option("startingOffsets", "latest") \
    .option("failOnDataLoss", "false") \
    .load()

# --- Base Processing: Deserialize and Add Timestamp ---
deserialized_df = kafka_df.withColumn("deserialized_value", deserialize_json_udf(col("value"), col("topic")))

base_df = deserialized_df.select(
    to_timestamp(col("deserialized_value.timestamp")).alias("event_time"),
    col("deserialized_value.level").alias("level"),
    col("deserialized_value.message").alias("message")
).withWatermark("event_time", "10 seconds")


# --- NEW: Enrichment Logic for IT Incidents ---
# We use efficient regular expressions to extract details instead of the old UDF.
# Replace the existing enriched_df block with this one

enriched_df = base_df.withColumn(
    # This pattern is now more specific and will not fail
    "incident_id", regexp_extract(col("message"), r"(INC-[A-F0-9]+)", 1)
).withColumn(
    # This pattern is now more specific
    "service", regexp_extract(col("message"), r"Service: (\S+?)(?:\sDOWN|\.|$|,)", 1)
).withColumn(
    # This pattern is more robust to handle different sentence endings
    "category", regexp_extract(col("message"), r"Category: ([\w\s]+?)(?:\.|$|,)", 1)
)

# --- NEW: Aggregation for Incident Alerting ---
# We group by a 5-minute window and the incident level.
aggregated_df = enriched_df \
    .groupBy(
        window(col("event_time"), "5 minutes"),
        col("level")
    ).count()


# --- NEW: Alerting Logic for High-Severity Incidents ---
# --- CORRECTED Alerting Logic ---
def process_alerts_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    print(f"--- Processing Alerts Batch {batch_id} ---")
    
    # Flatten the window struct BEFORE converting to Pandas
    pandas_df = batch_df.select(
        col("window.start").alias("window_start"),
        col("window.end").alias("window_end"),
        col("level"),
        col("count")
    ).toPandas()

    if pandas_df.empty:
        return

    # Now, this loop will work correctly
    for row in pandas_df.itertuples():
        if row.level == "ERROR" and row.count >= 3:
            alert_message = f"ALERT: High number of critical incidents! {row.count} ERRORs detected between {row.window_start} and {row.window_end}."
            print(f"\n\033[91m{alert_message}\033[0m\n")

# --- NEW: Function to Write Enriched Incident Data to Hourly Files ---
def write_enriched_to_hourly_csv(batch_df, batch_id):
    if batch_df.isEmpty(): return

    # Use current time to create a unique file for each hour
    hourly_file_suffix = datetime.now().strftime("%Y-%m-%d_%H")
    output_file_path = os.path.join(OUTPUT_PATH_ENRICHED, f"incidents_{hourly_file_suffix}.csv")
    
    print(f"Batch {batch_id}: Writing {batch_df.count()} enriched incident rows to {output_file_path}")

    # Coalesce to 1 partition before collecting to Pandas
    pandas_df = batch_df.coalesce(1).toPandas()

    # Append to the hourly file, writing the header only if the file is new
    file_exists = os.path.exists(output_file_path)
    pandas_df.to_csv(output_file_path, mode='a', header=not file_exists, index=False)


# --- Start the Streaming Queries ---
# Query 1: Writes the raw enriched data
enriched_query = enriched_df.writeStream \
    .foreachBatch(write_enriched_to_hourly_csv) \
    .outputMode("append") \
    .trigger(processingTime='1 minute') \
    .option("checkpointLocation", CHECKPOINT_PATH_ENRICHED) \
    .start()

# Query 2: Processes aggregations for alerting
alerting_query = aggregated_df.writeStream \
    .foreachBatch(process_alerts_batch) \
    .outputMode("update") \
    .trigger(processingTime='1 minute') \
    .option("checkpointLocation", CHECKPOINT_PATH_ALERTS) \
    .start()

print("Streaming queries for IT Incidents started. Waiting for termination...")
spark.streams.awaitAnyTermination()