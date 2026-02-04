# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from buffering stdout/stderr (important for logs)
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run the web service on container startup
# Cloud Run expects the container to listen on $PORT
# Using 2 workers for basic concurrency reliability
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 2
