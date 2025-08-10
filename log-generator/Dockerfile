FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code AND the new entrypoint script
COPY log_generator.py log_generator.py
COPY docker-entrypoint.sh docker-entrypoint.sh

# Set the entrypoint to our new script.
# The original command is now the CMD, which gets passed as arguments to the entrypoint.
ENTRYPOINT ["./docker-entrypoint.sh"]
CMD ["python", "-u", "log_generator.py"]