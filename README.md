# Real-Time Incident Management & AI Analysis Pipeline (v1.0)

This project demonstrates a complete, end-to-end, real-time data pipeline designed to ingest, process, orchestrate, and analyze IT incident logs. The pipeline culminates in an interactive dashboard where incidents can be submitted to Google's Gemini 2.5 Pro for a sophisticated, AI-powered root cause analysis and a recommended action plan.

This repository is an ideal learning resource for data engineers, DevOps engineers, and SREs interested in modern data stacks and the practical application of GenAI in operations.

## Architecture Diagram

graph TD
    subgraph User Interaction
        U(User)
    end

    subgraph Orchestration Layer [Apache Airflow]
        A_UI(Airflow Web UI) --> A_SCH(Airflow Scheduler)
        A_SCH --> A_DB[(PostgreSQL DB)]
        A_SCH --> A_DAG(stream_orch_dag.py)
    end
    
    subgraph Data Pipeline
        direction LR
        subgraph Data Generation
            LG(log-generator.py)
        end
        subgraph Ingestion [Kafka]
            K(Kafka Broker <br> Topic: incidents)
        end
        subgraph Processing [Spark]
            SM(Spark Master) --> SW(Spark Worker)
            SW --> SPARK_APP(stream_processing.py)
        end
        subgraph Storage
            CSV[(Hourly CSV Files)]
        end
    end

    subgraph AI Analysis [Streamlit & Gemini]
        DASH(Tamer AI Dashboard)
        API{Gemini 1.5 Pro API}
    end

    %% Define High-Level Connections
    U -- "Monitors & Triggers" --> A_UI
    
    A_DAG -- "Starts" --> LG
    A_DAG -- "Submits Job" --> SM
    
    LG -- "Sends Logs" --> K
    SPARK_APP -- "Consumes Logs" --> K
    SPARK_APP -- "Writes Processed CSVs" --> CSV
    
    DASH -- "Reads CSVs" --> CSV
    U -- "Views & Analyzes" --> DASH
    DASH -- "API Request" --> API
    API -- "Returns Analysis" --> DASH

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

## ⚡ Quick Start with `make`

For experienced users who have the prerequisites installed, you can get the entire pipeline running with these simple commands:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/tamereissa77/incident-mgmt-app-V1.0.git
    cd incident-mgmt-app-V1.0
    ```
2.  **Create your environment file:**
    Create a file named `.env` and add your `GEMINI_API_KEY`.
    ```
    GEMINI_API_KEY=your_google_api_key_here
    ```
3.  **Start the pipeline:**
    ```bash
    make start
    ```
4.  **Trigger the workflow:**
    ```bash
    make trigger-dag
    ```
5.  **Access the Dashboard:**
    -   **AI Dashboard:** **[http://localhost:8501](http://localhost:8501)**
    -   **Airflow UI:** **[http://localhost:8070](http://localhost:8070)** (user: `admin`, pass: `admin`)

---
## ✨ Features

-   **Real-Time Data Ingestion:** A Python script generates realistic IT incident logs and produces them to a Kafka topic.
-   **Scalable Messaging:** A single-broker Kafka cluster (easily scalable) acts as the central, fault-tolerant message bus.
-   **Stream Processing:** An Apache Spark Structured Streaming job consumes logs from Kafka in real-time, enriches the data by parsing messages, and writes the results to a storage layer.
-   **Workflow Orchestration:** Apache Airflow manages the entire pipeline, from starting the data producer to submitting the Spark processing job.
-   **Interactive AI Dashboard:** A Streamlit web application provides a real-time view of processed incidents, allowing users to select an incident for deeper analysis.
-   **AI-Powered Root Cause Analysis:** Integration with the **Google Gemini 1.5 Pro API** to provide expert-level root cause analysis, generate a plausible timeline of events, and recommend a detailed action plan.
-   **Fully Containerized:** The entire stack is defined in `docker-compose.yml`, ensuring easy setup, portability, and consistent environments.

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed on your system:

-   **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: The entire application stack runs in Docker containers.
-   **WSL 2 (for Windows users)**: Docker Desktop on Windows requires the Windows Subsystem for Linux 2.
    -   **Important:** Ensure your WSL 2 is allocated sufficient resources. A minimum of **8GB of memory** is recommended. You can configure this in a `.wslconfig` file in your user profile directory (`%userprofile%`).
-   **[Git](https://git-scm.com/)**: For cloning the repository.
-   **Make (for Windows users)**: To use the `Makefile`, you may need to install `make`. This can be done easily via [Chocolatey](https://chocolatey.org/) by running `choco install make`.

---

## ▶️ How to Run the Pipeline (with `make`)

This project uses a `Makefile` to simplify the Docker Compose commands.

### 1. Clone the Repository & Configure API Key

First, clone the repository and create your `.env` file for the Gemini API key.

```bash
git clone https://github.com/tamereissa77/incident-mgmt-app-V1.0.git
cd incident-mgmt-app-V1.0
```

Create a file named `.env` and add your key:
```
GEMINI_API_KEY=your_google_api_key_here
```

### 2. Start the Pipeline

This single command builds the necessary Docker images and starts all the services in the background.

```bash
make start
```

### 3. Trigger the Pipeline Workflow

The infrastructure is running, but the data flow is initiated by Airflow. Trigger the main DAG with this command:

```bash
make trigger-dag
```

The `log-generator` will now start producing data, and the Spark job will begin processing it.

### 4. Monitor and Analyze

-   **Check the status of all services:**
    ```bash
    make status
    ```
-   **Follow the logs of a specific service:**
    ```bash
    make logs-airflow
    make logs-spark
    make logs-producer
    ```
-   **Open the dashboards** to view the pipeline in action.

---

## 🌐 Accessing Services

The pipeline exposes several UIs for monitoring and interaction:

| Service                       | URL                                     | Description                               |
| ----------------------------- | --------------------------------------- | ----------------------------------------- |
| **Tamer Analysis Dashboard**  | **[http://localhost:8501](http://localhost:8501)** | **Main application UI for AI analysis.**    |
| **Airflow UI**                | [http://localhost:8070](http://localhost:8070) | Orchestration and DAG monitoring.         |
| **Spark Master UI**           | [http://localhost:8080](http://localhost:8080) | View running and completed Spark jobs.    |
| **Confluent Control Center**  | [http://localhost:9021](http://localhost:9021) | Monitor Kafka topics and message flow.    |

---

## ⏹️ Stopping the Pipeline

### Graceful Stop

This command will stop and remove all the running containers for this project. Your data volumes (Kafka data, PostgreSQL DB) will be preserved.

```bash
make down
```

### Deep Clean

This command will stop and remove everything: containers, the Docker network, **and all data volumes**. Use this when you want a completely fresh start.

```bash
make clean
```
*(You will be asked to confirm before data is deleted.)*

---
