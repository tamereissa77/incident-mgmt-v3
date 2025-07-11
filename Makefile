# Makefile for the Real-Time Incident Management & AI Analysis Pipeline
# Done by TAMER ABDELFATTAH

# Use bash for better command handling
SHELL := /bin/bash

# Define color codes for better output readability
GREEN := \033[0;32m
YELLOW := \033[0;33m
NC := \033[0m

.PHONY: help build up start down clean logs status test-producer test-spark

# Default target when 'make' is run without arguments
default: help

help:
	@echo -e "$(GREEN)Available commands for the Incident Management Pipeline:$(NC)"
	@echo "--------------------------------------------------------"
	@echo "  $(YELLOW)make build$(NC)           -> Build or rebuild all custom Docker images (dashboard, spark, log-generator)."
	@echo "  $(YELLOW)make up$(NC)               -> Start all services in detached (background) mode."
	@echo "  $(YELLOW)make start$(NC)            -> A convenient alias for 'build' and 'up'."
	@echo "  $(YELLOW)make down$(NC)             -> Stop and remove all running containers for this project."
	@echo "  $(YELLOW)make clean$(NC)            -> Perform a deep clean: stop/remove containers, volumes, and networks."
	@echo "  $(YELLOW)make logs$(NC)             -> Follow the logs for all running services."
	@echo "  $(YELLOW)make logs-airflow$(NC)      -> Follow the logs specifically for the Airflow scheduler."
	@echo "  $(YELLOW)make logs-spark$(NC)        -> Follow the logs specifically for the Spark master."
	@echo "  $(YELLOW)make logs-producer$(NC)     -> Follow the logs specifically for the log-generator."
	@echo "  $(YELLOW)make status$(NC)           -> Show the status of all running containers."
	@echo "  $(YELLOW)make trigger-dag$(NC)      -> Manually trigger the main processing pipeline DAG."
	@echo "--------------------------------------------------------"

# Target to build all custom Docker images
build:
	@echo -e "$(GREEN)--> Building all custom Docker images...$(NC)"
	docker-compose build

# Target to start all services in detached mode
up:
	@echo -e "$(GREEN)--> Starting all services in the background...$(NC)"
	docker-compose up -d

# Target to build and then start all services
start: build up
	@echo -e "$(GREEN)--> Pipeline started successfully! Use 'make status' to check services.$(NC)"
	@echo "--> Access your dashboards:"
	@echo "    - AI Dashboard: http://localhost:8501"
	@echo "    - Airflow UI:   http://localhost:8070"
	@echo "    - Spark UI:     http://localhost:8080"
	@echo "    - Kafka UI:     http://localhost:9021"

# Target to stop and remove containers
down:
	@echo -e "$(GREEN)--> Stopping and removing containers...$(NC)"
	docker-compose down

# Target to perform a deep clean, including volumes and networks
clean:
	@echo -e "$(YELLOW)--> WARNING: This will stop all services and delete all data (Kafka topics, Airflow metadata).$(NC)"
	@read -p "Are you sure you want to continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo -e "$(GREEN)--> Performing deep clean...$(NC)"; \
		docker-compose down -v --remove-orphans; \
	else \
		echo "Clean operation cancelled."; \
	fi

# Target to view logs from all services
logs:
	@echo -e "$(GREEN)--> Tailing logs for all services (Press Ctrl+C to exit)...$(NC)"
	docker-compose logs -f

# Target to view logs from the Airflow scheduler
logs-airflow:
	@echo -e "$(GREEN)--> Tailing logs for the Airflow scheduler (Press Ctrl+C to exit)...$(NC)"
	docker-compose logs -f airflow-scheduler

# Target to view logs from the Spark master
logs-spark:
	@echo -e "$(GREEN)--> Tailing logs for the Spark master (Press Ctrl+C to exit)...$(NC)"
	docker-compose logs -f spark-master

# Target to view logs from the log producer
logs-producer:
	@echo -e "$(GREEN)--> Tailing logs for the log-generator (Press Ctrl+C to exit)...$(NC)"
	docker-compose logs -f log-generator

# Target to show the status of running containers
status:
	@echo -e "$(GREEN)--> Current status of all services:$(NC)"
	docker-compose ps

# Target to manually trigger the Airflow DAG
trigger-dag:
	@echo -e "$(GREEN)--> Manually triggering the 'incident_processing_pipeline' DAG...$(NC)"
	docker-compose exec airflow-webserver airflow dags trigger incident_processing_pipeline
