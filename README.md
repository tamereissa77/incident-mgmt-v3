# Real-Time Incident Management & AI Analysis Pipeline (v1.0)

This project demonstrates a complete, end-to-end, real-time data pipeline designed to ingest, process, orchestrate, and analyze IT incident logs. The pipeline culminates in an interactive dashboard where incidents can be submitted to Google's Gemini 2.5 Pro for a sophisticated, AI-powered root cause analysis and a recommended action plan.

This repository is an ideal learning resource for data engineers, DevOps engineers, and SREs interested in modern data stacks and the practical application of GenAI in operations.

## Architecture Diagram

The pipeline is composed of several key components that work in concert, as illustrated below:

![Architecture Diagram](httpsp://i.imgur.com/gK5eZlA.png)
*(Assuming you will place the architecture image in an `assets` folder or link to it)*

## ✨ Features

-   **Real-Time Data Ingestion:** A Python script generates realistic IT incident logs and produces them to a Kafka topic.
-   **Scalable Messaging:** A single-broker Kafka cluster (easily scalable) acts as the central, fault-tolerant message bus.
-   **Stream Processing:** An Apache Spark Structured Streaming job consumes logs from Kafka in real-time, enriches the data by parsing messages, and writes the results to a storage layer.
-   **Workflow Orchestration:** Apache Airflow manages the entire pipeline, from starting the data producer to submitting the Spark processing job.
-   **Interactive AI Dashboard:** A Streamlit web application provides a real-time view of processed incidents, allowing users to select an incident for deeper analysis.
-   **AI-Powered Root Cause Analysis:** Integration with the **Google Gemini 2.5 Pro API** to provide expert-level root cause analysis, generate a plausible timeline of events, and recommend a detailed action plan.
-   **Fully Containerized:** The entire stack is defined in `docker-compose.yml`, ensuring easy setup, portability, and consistent environments.

## 🛠️ Technology Stack

| Component                 | Technology                                                                          | Purpose                                                              |
| ------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| **Orchestration**         | [Apache Airflow](https://airflow.apache.org/)                                       | Scheduling and managing the entire pipeline workflow (DAGs).         |
| **Data Ingestion**        | [Apache Kafka](https://kafka.apache.org/) (Confluent Platform)                      | High-throughput, distributed streaming platform.                     |
| **Schema Management**     | [Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html) | Enforces data structure and schema evolution.                          |
| **Stream Processing**     | [Apache Spark](https://spark.apache.org/) (Structured Streaming)                    | Real-time data transformation, enrichment, and analysis.             |
| **AI Analysis**           | [Google Gemini 2.5 Pro](https://deepmind.google/technologies/gemini/)                 | Root cause analysis, timeline generation, and action plan recommendation. |
| **Dashboard**             | [Streamlit](https://streamlit.io/)                                                  | Building the interactive web application for incident analysis.      |
| **Containerization**      | [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/) | Containerizing all services for a consistent and portable setup.     |
| **Metadata Database**     | [PostgreSQL](https://www.postgresql.org/)                                           | Backend database for Apache Airflow.                               |

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: The entire application stack runs in Docker containers.
-   **WSL 2 (for Windows users)**: Docker Desktop on Windows requires the Windows Subsystem for Linux 2.
    -   **Important:** Ensure your WSL 2 is allocated sufficient resources. A minimum of **8GB of memory** is recommended. You can configure this in a `.wslconfig` file in your user profile directory (`%userprofile%`).
-   **[Git](https://git-scm.com/)**: For cloning the repository.

## 🚀 Setup and Installation

Follow these steps to get the pipeline running on your local machine.

### 1. Clone the Repository

```bash
git clone https://github.com/tamereissa77/incident-mgmt-app-V1.0.git
cd incident-mgmt-app-V1.0
```

### 2. Configure the Gemini API Key

You need a Google Gemini API key to enable the AI analysis feature.

1.  Obtain your API key from [Google AI Studio](https://aistudio.google.com/).
2.  In the root directory of the project, create a new file named `.env`.
3.  Add your API key to the `.env` file like this:

    ```
    # .env file
    GEMINI_API_KEY=your_super_secret_api_key_here
    ```
4.  The `docker-compose.yml` file is already configured to read this variable and pass it securely to the dashboard container.

## ▶️ How to Run the Pipeline

The entire pipeline is managed via Docker Compose.

### 1. Build the Custom Images

This command will build the Docker images for the `log-generator`, `spark`, and `dashboard` services based on their respective Dockerfiles.

```bash
docker-compose build
```

### 2. Start All Services

This command will start all services (Kafka, Spark, Airflow, Dashboard, etc.) in the background.

```bash
docker-compose up -d
```

### 3. Trigger the Airflow DAG

The infrastructure is now running, but the pipeline itself is dormant. You must trigger it from the Airflow UI.

1.  Navigate to the **Airflow UI**: **[http://localhost:8070](http://localhost:8070)**
2.  Login with username `admin` and password `admin`.
3.  On the homepage, find the DAG named `incident_processing_pipeline`.
4.  Un-pause the DAG using the toggle switch on the left.
5.  Click the **Play (▶️)** button on the right to trigger a new DAG run.

This will kick off the entire process: the log generator will start producing data, and the Spark job will be submitted to process it.

## 🌐 Accessing Services

The pipeline exposes several UIs for monitoring and interaction:

| Service                       | URL                                     | Description                               |
| ----------------------------- | --------------------------------------- | ----------------------------------------- |
| **Tamer Analysis Dashboard**  | **[http://localhost:8501](http://localhost:8501)** | **Main application UI for AI analysis.**    |
| **Airflow UI**                | [http://localhost:8070](http://localhost:8070) | Orchestration and DAG monitoring.         |
| **Spark Master UI**           | [http://localhost:8080](http://localhost:8080) | View running and completed Spark jobs.    |
| **Confluent Control Center**  | [http://localhost:9021](http://localhost:9021) | Monitor Kafka topics and message flow.    |

## 📂 Project Structure

```
.
├── airflow/
│   ├── dags/
│   │   └── stream_orch_dag.py        # The main Airflow DAG for orchestration
│   └── plugins/
├── dashboard/
│   ├── dashboard.py                  # The Streamlit application code
│   ├── Dockerfile
│   └── requirements.txt
├── log-generator/
│   ├── log_generator.py              # The Python script that produces Kafka messages
│   ├── Dockerfile
│   └── requirements.txt
├── spark/
│   ├── additional-jars/              # For Spark-Kafka connector JARs
│   ├── spark-apps/
│   │   └── stream_processing.py      # The PySpark Structured Streaming application
│   └── spark-data/                   # Mounted volume for Spark output (CSVs, checkpoints)
├── .env                              # For storing API keys securely (you must create this)
├── .gitignore                        # Specifies files/directories for Git to ignore
├── docker-compose.yml                # Defines and configures all services
└── README.md                         # You are here!
```

## 💡 Troubleshooting Common Issues

-   **`Connection refused` or `Name or service not known` errors in logs:** This usually indicates a service (like Kafka) crashed or failed to start.
    -   **Solution:** Ensure Docker Desktop has enough resources (at least 8GB RAM). Use the simplified single-broker configuration in `docker-compose.yml` if necessary. Run `docker-compose down -v` to fully reset the environment.
-   **`DuplicateWidgetID` error in Streamlit:** This is caused by using a `while True:` loop for refreshing.
    -   **Solution:** Remove the loop. Streamlit's execution model handles re-runs. Use `st.html` for a JavaScript-based auto-refresh if needed.
-   **`ModuleNotFoundError` in a container:** A service fails because a Python package is missing.
    -   **Solution:** Add the missing package to the correct `requirements.txt` file (e.g., `dashboard/requirements.txt`) and rebuild the image with `docker-compose build --no-cache <service_name>`.
-   **Airflow DAG tasks fail:**
    -   **Solution:** Click on the failed task (red square) in the Airflow UI Grid View, then click "Logs" to see the specific error message from the task's execution. This is the most effective way to debug DAG issues.
