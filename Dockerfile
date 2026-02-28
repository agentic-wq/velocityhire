# VelocityHire — Dockerfile
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install all agent/demo dependencies
COPY agent1/requirements.txt agent1_requirements.txt
COPY agent2/requirements.txt agent2_requirements.txt
COPY agent3/requirements.txt agent3_requirements.txt
COPY demo/requirements.txt demo_requirements.txt
RUN pip install --no-cache-dir \
    -r agent1_requirements.txt \
    -r agent2_requirements.txt \
    -r agent3_requirements.txt \
    -r demo_requirements.txt

# Copy entire project
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MOCK_MODE=true
ENV PYTHONPATH=/app/agent1:/app/agent2:/app/agent3:/app

# Expose port
EXPOSE 8080

# Start the demo app with Uvicorn
CMD ["sh", "-c", "uvicorn demo.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
