#!/bin/sh
# This script is the new entrypoint for the log-generator container.

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Entrypoint script started. Waiting 20 seconds for Kafka and Schema Registry to be fully ready..."
sleep 20

echo "Waited 20 seconds. Now executing the main application command..."
# The "$@" part means "execute all the arguments that were passed to this script".
# In our Dockerfile, this will be ["python", "-u", "log_generator.py"].
exec "$@"