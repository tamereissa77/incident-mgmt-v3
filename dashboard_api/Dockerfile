# /dashboard_api/Dockerfile
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# ADD THIS BLOCK: Install system dependencies needed to build pandas
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*
# END OF ADDED BLOCK

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --timeout=600 -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on
EXPOSE 8000

# The command to start the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]