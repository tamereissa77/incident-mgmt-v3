# Real-Time SRE Insight Engine with GenAI (v2.0)

This project demonstrates a complete, end-to-end, real-time data pipeline designed to ingest, process, and analyze IT incident logs. The architecture has been upgraded to a modern, decoupled system featuring a **FastAPI backend** and a **React frontend**, with the entire application stack managed and served by Docker.

The pipeline culminates in a sophisticated "iPulse SRE" dashboard. This modern web application provides a live feed of incidents, an AI-powered analysis page for deep root cause investigation using **Google's Gemini 1.5 Pro**, and an intelligent, context-aware Chat Assistant.

This repository serves as a professional template for building scalable, real-time analytics platforms and showcases the practical application of GenAI in modern SRE and DevOps operations.

## Architecture Diagram
*(You can update this with a new diagram reflecting the React UI and FastAPI service)*
<img width="3379" height="3840" alt="technical diagram" src="https://github.com/user-attachments/assets/01ca4bf7-bf9a-41d2-8384-7077923d117e" />

## ✨ Features

-   **Decoupled Frontend/Backend Architecture:**
    -   **Modern React UI:** A responsive and interactive user interface built with React, Vite, and Tailwind CSS, providing a professional SRE experience.
    -   **High-Performance FastAPI Backend:** A robust Python backend serves data and handles AI integration, ensuring a clean separation of concerns.
-   **Real-Time Data Pipeline:**
    -   A continuous Python script generates realistic IT incident logs and produces them to Kafka.
    -   A single-broker Kafka cluster acts as the central, fault-tolerant message bus.
    -   An Apache Spark Structured Streaming job consumes logs, enriches data with robust regex parsing, and appends results to a persistent storage layer.
-   **Intelligent AI Features:**
    -   **AI Root Cause Analysis:** Select any incident for a deep analysis by Google's Gemini 1.5 Pro, which generates a structured report with a summary, timeline, root cause, and action plan.
    -   **Context-Aware Chat Assistant:** An AI chatbot with conversation memory that uses the latest incident data to provide relevant troubleshooting advice and situational summaries.
-   **Fully Containerized for Production:** The entire stack, including the Nginx-served React frontend, is defined in a single `docker-compose.yml` file for one-command startup and deployment.
-   **Workflow Orchestration:** Apache Airflow manages the pipeline, ensuring data producers and processors run in the correct order.

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| **Frontend UI** | **React (Vite), Tailwind CSS** | Modern, responsive user interface for visualization and interaction. |
| **Backend API** | **FastAPI** | High-performance Python API to serve data and connect to AI services. |
| **Web Server** | **Nginx** | Serves the production-built static frontend files. |
| **Orchestration** | Apache Airflow | Scheduling and managing the entire pipeline workflow. |
| **Data Ingestion** | Apache Kafka (Confluent) | High-throughput, distributed streaming platform. |
| **Schema Mgmt** | Confluent Schema Registry | Enforces data structure and schema evolution. |
| **Stream Processing**| Apache Spark | Real-time data transformation, enrichment, and analysis. |
| **AI Analysis** | Google Gemini 1.5 Pro | Root cause analysis and intelligent chat responses. |
| **Containerization**| Docker & Docker Compose | Containerizing all services for a consistent, portable, one-command setup. |
| **Metadata DB** | PostgreSQL | Backend database for Apache Airflow. |

## 📋 Prerequisites

-   **[Docker Desktop](https://www.docker.com/products/docker-desktop/)**: The entire application stack runs in Docker containers.
-   **WSL 2 (for Windows users)**: Docker Desktop on Windows requires WSL 2. A minimum of **8-12GB of memory** allocated to WSL is recommended.
-   **[Git](https://git-scm.com/)**: For cloning the repositories.
-   **Make (Optional)**: A `Makefile` is included for convenient shortcuts. On Windows, you can install it via [Chocolatey](https://chocolatey.org/) (`choco install make`).

## 🚀 Setup and Installation

This project consists of two separate repositories that work together.

### 1. Clone Both Repositories

Clone both the backend and frontend repositories so they are in the **same parent directory**.

```bash
# In your main projects folder (e.g., /vscodes/)
git clone https://github.com/tamereissa77/incedentMGR-V2.git
git clone https://github.com/tamereissa77/ai-sre-insight.git
```
Your folder structure should look like this:
```
/vscodes/
├── incedentMGR-V2/
└── ai-sre-insight/
```

### 2. Configure the Gemini API Key

1.  Obtain your API key from [Google AI Studio](https://aistudio.google.com/).
2.  Navigate into the backend repository: `cd incedentMGR-V2`.
3.  Create a new file named `.env`.
4.  Add your API key to the `.env` file:
    ```
    GEMINI_API_KEY=your_super_secret_api_key_here
    ```

## ▶️ How to Run the Entire Application

The entire application is managed from the backend repository's `docker-compose.yml`.

### 1. Build and Start All Services

Navigate to the backend repository and use the `make` command. This single command will build all custom Docker images (including the frontend UI) and start all services in the background.

```bash
cd /path/to/your/incedentMGR-V2
make up --build
```
*(Use `--build` the first time or whenever you change a Dockerfile. Afterwards, you can just use `make up`.)*

### 2. Trigger the Data Pipeline

The infrastructure is now running, but the data flow must be started via Airflow.

1.  Navigate to the **Airflow UI**: **[http://localhost:8070](http://localhost:8070)**
2.  Login with username `admin` and password `admin`.
3.  On the homepage, find the DAG `incident_processing_pipeline`, un-pause it, and click the **Play (▶️)** button to trigger a run.

The `log-generator` will now start producing data continuously, and the Spark job will begin processing it.

## 🌐 Accessing Services

| Service | URL | Description |
|---|---|---|
| **iPulse SRE Dashboard** | **[http://localhost:3000](http://localhost:3000)** | **Main application UI.** |
| **Backend API Docs** | [http://localhost:7000/docs](http://localhost:7000/docs)| Interactive API documentation (Swagger UI). |
| **Airflow UI** | [http://localhost:8070](http://localhost:8070) | Orchestration and DAG monitoring. |
| **Spark Master UI** | [http://localhost:8080](http://localhost:8080) | View running and completed Spark jobs. |
| **Confluent Control Center**| [http://localhost:9021](http://localhost:9021) | Monitor Kafka topics and message flow. |

## ⏹️ Stopping the Pipeline

### Graceful Stop

This command stops and removes all running containers. Your data volumes (Kafka, PostgreSQL) will be preserved.

```bash
make down
```

### Deep Clean

This command stops and removes everything: containers, networks, **and all data volumes**. Use this for a completely fresh start.

```bash
make clean
```

## 📂 Project Structure (`incedentMGR-V2`)

```
.
├── dashboard_api/          # The FastAPI backend service
│   ├── main.py
│   ├── Dockerfile
│   └── requirements.txt
├── log-generator/          # The Kafka data producer
│   ├── log_generator.py
│   ├── docker-entrypoint.sh
│   └── Dockerfile
├── spark/                  # The Spark stream processing job
│   └── spark-apps/
│       └── stream_processing.py
├── airflow/
│   └── dags/
│       └── stream_orch_dag.py
├── .env                    # For storing API keys securely (created by you)
├── docker-compose.yml      # Defines and orchestrates ALL services, including the frontend
└── Makefile                # Convenient shortcuts for docker-compose commands
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
    -   **AI Dashboard:** **[http://localhost:3000](http://localhost:3000)**
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
### MAIN DASHBOARD
<img width="1543" height="822" alt="image" src="https://github.com/user-attachments/assets/2a0448a2-4818-4ade-b00b-9d496fb18824" />

### LIVE INCIDENTS
<img width="1338" height="915" alt="image" src="https://github.com/user-attachments/assets/6255118e-fdd4-4b47-b8c7-f982e39b4a44" />

### AI ANALYSIS
<img width="1352" height="932" alt="image" src="https://github.com/user-attachments/assets/4df4beb2-fb39-4e98-9751-8f391de3c225" />

### CHAT ASSISTANT
<img width="1348" height="937" alt="image" src="https://github.com/user-attachments/assets/193fb4bf-353d-405b-a8a6-d2138ae502e2" />

