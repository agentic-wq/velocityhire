# VelocityHire Quiz — Dockerfile
# Serves the static quiz files via a lightweight Python HTTP server.
# Compatible with Google Cloud Run (reads PORT from the environment).
FROM python:3.12-slim

WORKDIR /app

# Copy quiz files (HTML, JS, CSS, server)
COPY . .

ENV PYTHONUNBUFFERED=1

# Cloud Run injects PORT=8080; the server falls back to 3004 for local use.
EXPOSE 8080

CMD ["python", "server.py"]
