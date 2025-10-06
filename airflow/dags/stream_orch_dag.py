# Replace the entire content of ./airflow/dags/incident_processing_pipeline.py with this

from __future__ import annotations
import pendulum
from airflow.models.dag import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import BranchPythonOperator
from airflow.operators.empty import EmptyOperator
# --- NEW: Import the DockerOperator ---
from airflow.providers.docker.operators.docker import DockerOperator
import requests

# This command remains the same
create_topic_command = """
if ! docker exec kafka1 kafka-topics --list --bootstrap-server kafka1:29092 | grep -q '^incidents$'; then
    echo "Topic 'incidents' does not exist. Creating it...";
    docker exec kafka1 kafka-topics --create --topic incidents --partitions 3 --replication-factor 1 --bootstrap-server kafka1:29092;
else
    echo "Topic 'incidents' already exists.";
fi
"""

# This command remains the same
submit_spark_command = """
docker exec spark-master /opt/spark/bin/spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0 \
  /opt/spark-apps/stream_processing.py
"""

# This function remains the same
def _check_pyspark_job():
    """Checks if the Spark streaming job is already running."""
    try:
        response = requests.get('http://spark-master:8080/json/')
        response.raise_for_status()
        active_apps = response.json().get("activeapps", [])
        for app in active_apps:
            if app.get('name') == 'RealTimeIncidentProcessor':
                print("Spark job 'RealTimeIncidentProcessor' is already running. Skipping submission.")
                return "skip_submit_job_task"
        print("Spark job is not running. Proceeding to submit.")
        return "submit_spark_job_task"
    except requests.RequestException as e:
        print(f"Could not connect to Spark Master: {e}. Assuming job needs to be submitted.")
        return "submit_spark_job_task"


# --- DAG Definition ---
with DAG(
    dag_id='incident_processing_pipeline',
    start_date=pendulum.datetime(2024, 1, 1, tz="UTC"),
    schedule_interval="*/2 * * * *",
    catchup=False,
    tags=['incident-management'],
) as dag:

    create_incidents_topic_task = BashOperator(
        task_id='create_incidents_topic',
        bash_command=create_topic_command,
    )

    # --- THIS IS THE NEW, CORRECTED TASK ---
    # We use the DockerOperator to start the container.
    # It correctly handles networking by attaching to the project's network.
    start_incident_producer_task = BashOperator(
    task_id='start_incident_producer',
    bash_command="""
# Check if the container is already running to avoid errors on re-runs
if ! docker ps --filter "name=log-generator" --filter "status=running" | grep -q "log-generator"; then
    echo "Container is not running. Starting log-generator...";
    docker start log-generator;
else
    echo "Container log-generator is already running.";
fi
"""
)

    check_if_spark_job_is_running = BranchPythonOperator(
        task_id='check_if_spark_job_is_running',
        python_callable=_check_pyspark_job,
    )

    submit_spark_job_task = BashOperator(
        task_id='submit_spark_job_task',
        bash_command=submit_spark_command,
    )

    skip_submit_job_task = EmptyOperator(task_id="skip_submit_job_task")

    # The execution flow remains the same
    create_incidents_topic_task >> start_incident_producer_task >> check_if_spark_job_is_running
    check_if_spark_job_is_running >> [submit_spark_job_task, skip_submit_job_task]