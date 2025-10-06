# Use the official Spark image that includes Python 3
FROM apache/spark:3.5.0-python3

# Switch to root user IMMEDIATELY to perform all system-level installations.
USER root

# Run the package download script as root.
RUN \
  echo "Downloading Spark packages..." && \
  ($SPARK_HOME/bin/spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 --class org.apache.spark.examples.SparkPi dummy.jar 10 || true) && \
  echo "Copying downloaded JARs to Spark's main directory..." && \
  cp /root/.ivy2/jars/org.apache.spark_spark-sql-kafka-0-10_2.12-*.jar "$SPARK_HOME/jars/" && \
  cp /root/.ivy2/jars/org.apache.spark_spark-token-provider-kafka-0-10_2.12-*.jar "$SPARK_HOME/jars/" && \
  cp /root/.ivy2/jars/org.apache.commons_commons-pool2-*.jar "$SPARK_HOME/jars/" && \
  cp /root/.ivy2/jars/org.apache.kafka_kafka-clients-*.jar "$SPARK_HOME/jars/" && \
  echo "JARs copied successfully."

# Create and set permissions for your data directories.
RUN mkdir -p /opt/spark-data/data/enriched_incidents_hourly && \
    mkdir -p /opt/spark-data/spark_checkpoints/enriched_incidents_checkpoint && \
    mkdir -p /opt/spark-data/spark_checkpoints/alerts_checkpoint && \
    chmod -R 777 /opt/spark-data

# Install system dependencies.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    librdkafka-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory for the application
WORKDIR /opt/spark-apps

# Copy the requirements file
COPY ./spark-apps/requirements.txt /opt/spark-apps/requirements.txt

# Install the Python packages.
RUN python3 -m pip install "confluent-kafka==1.9.2" && \
    python3 -m pip install -r requirements.txt

