# Start from the official Airflow image
FROM apache/airflow:2.10.5

# The default user in this image is already 'airflow'.
# We can install packages directly without changing users.
RUN pip install --no-cache-dir "apache-airflow-providers-docker==3.9.1" "requests==2.31.0"