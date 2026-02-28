# VelocityHire — Containerisation & Google Cloud Run Deployment Guide

---

## Overview

This guide walks through containerising the VelocityHire application using Docker and deploying it to **Google Cloud Run** — a fully managed serverless container platform.

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed locally
- [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk/docs/install) installed
- A Google Cloud project with billing enabled
- Google Cloud APIs enabled:
  - Cloud Run API
  - Container Registry API (or Artifact Registry API)
  - Cloud Build API

```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
```

---

## Step 1 — Project Structure

Ensure your VelocityHire project root looks like this before containerising:

```
velocityhire/
├── demo/
│   └── app.py
├── agent1/
│   ├── agent_1.py
│   └── app.py
├── agent2/
│   ├── agent_2.py
│   └── app.py
├── agent3/
│   ├── agent_3.py
│   └── app.py
├── shared/
├── requirements.txt
├── Dockerfile          ← you will create this
├── .dockerignore       ← you will create this
└── .env                ← never committed to git
```

---

## Step 2 — Create the Dockerfile

Create a `Dockerfile` in the project root:

```dockerfile
# Use official Python slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV MOCK_MODE=true

# Expose port (Cloud Run injects $PORT automatically)
EXPOSE 8080

# Start the demo app with Uvicorn
CMD ["sh", "-c", "uvicorn demo.app:app --host 0.0.0.0 --port ${PORT:-8080}"]
```

> **Note:** Google Cloud Run injects a `$PORT` environment variable automatically. Always bind to `$PORT`, not a hardcoded port.

---

## Step 3 — Create .dockerignore

Create a `.dockerignore` file to keep the image lean:

```
.env
*.db
*.log
logs/
__pycache__/
*.pyc
*.pyo
.git/
.gitignore
downloads/
*.md
tests/
.pytest_cache/
```

---

## Step 4 — Update requirements.txt

Ensure the root `requirements.txt` includes all demo dependencies. Merge with `demo/requirements.txt` if needed:

```
fastapi==0.115.6
uvicorn[standard]==0.32.1
langgraph==0.2.60
langchain-core==0.3.28
python-dotenv==1.0.1
pydantic==2.10.3
httpx==0.27.2
sqlalchemy>=2.0.0
requests==2.32.3
gunicorn==21.2.0
```

---

## Step 5 — Build & Test Locally

```bash
# Build the Docker image
docker build -t velocityhire:latest .

# Run locally to test
docker run -p 8080:8080 -e PORT=8080 velocityhire:latest

# Visit http://localhost:8080 to verify
```

---

## Step 6 — Set Up Google Cloud Project

```bash
# Authenticate with Google Cloud
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Set your region
gcloud config set run/region europe-west1
```

> Replace `YOUR_PROJECT_ID` with your actual GCP project ID.
> Replace `europe-west1` with your preferred region (e.g. `us-central1`, `australia-southeast1`).

---

## Step 7 — Push Image to Google Artifact Registry

```bash
# Create an Artifact Registry repository
gcloud artifacts repositories create velocityhire \
    --repository-format=docker \
    --location=europe-west1 \
    --description="VelocityHire container images"

# Authenticate Docker with Artifact Registry
gcloud auth configure-docker europe-west1-docker.pkg.dev

# Tag the image
docker tag velocityhire:latest \
    europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/velocityhire/demo:latest

# Push the image
docker push \
    europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/velocityhire/demo:latest
```

---

## Step 8 — Deploy to Google Cloud Run

```bash
gcloud run deploy velocityhire \
    --image europe-west1-docker.pkg.dev/YOUR_PROJECT_ID/velocityhire/demo:latest \
    --platform managed \
    --region europe-west1 \
    --allow-unauthenticated \
    --memory 1Gi \
    --cpu 1 \
    --min-instances 0 \
    --max-instances 5 \
    --port 8080 \
    --set-env-vars MOCK_MODE=true
```

After deployment, Cloud Run will output a public URL like:
```
https://velocityhire-xxxxxxxxxx-ew.a.run.app
```

---

## Step 9 — Set Environment Variables (Secrets)

Never hardcode secrets. Use **Google Secret Manager** for sensitive values:

```bash
# Create a secret
echo -n "your-secret-value" | gcloud secrets create CLIENT_SECRET --data-file=-

# Grant Cloud Run access to the secret
gcloud secrets add-iam-policy-binding CLIENT_SECRET \
    --member="serviceAccount:YOUR_SERVICE_ACCOUNT@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Reference it in Cloud Run deployment
gcloud run deploy velocityhire \
    --set-secrets CLIENT_SECRET=CLIENT_SECRET:latest
```

---

## Step 10 — (Optional) Custom Domain

```bash
# Map a custom domain to the Cloud Run service
gcloud run domain-mappings create \
    --service velocityhire \
    --domain velocityhire.yourdomain.com \
    --region europe-west1
```

Then update your DNS provider with the CNAME/A records provided by GCP.

---

## Step 11 — (Optional) CI/CD with Cloud Build

Create a `cloudbuild.yaml` in the project root for automated deployments:

```yaml
steps:
  # Build the container image
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'build'
      - '-t'
      - 'europe-west1-docker.pkg.dev/$PROJECT_ID/velocityhire/demo:$COMMIT_SHA'
      - '.'

  # Push to Artifact Registry
  - name: 'gcr.io/cloud-builders/docker'
    args:
      - 'push'
      - 'europe-west1-docker.pkg.dev/$PROJECT_ID/velocityhire/demo:$COMMIT_SHA'

  # Deploy to Cloud Run
  - name: 'gcr.io/google.com/cloudsdktool/cloud-sdk'
    entrypoint: gcloud
    args:
      - 'run'
      - 'deploy'
      - 'velocityhire'
      - '--image'
      - 'europe-west1-docker.pkg.dev/$PROJECT_ID/velocityhire/demo:$COMMIT_SHA'
      - '--region'
      - 'europe-west1'
      - '--platform'
      - 'managed'

images:
  - 'europe-west1-docker.pkg.dev/$PROJECT_ID/velocityhire/demo:$COMMIT_SHA'
```

Trigger on every push to the `master` branch via Cloud Build triggers in GCP Console.

---

## Cost Estimate (Cloud Run)

| Resource | Free Tier | Est. Monthly Cost |
|----------|-----------|-------------------|
| CPU | 180,000 vCPU-seconds/month | ~$0 at low traffic |
| Memory | 360,000 GB-seconds/month | ~$0 at low traffic |
| Requests | 2M requests/month | ~$0 at low traffic |
| Beyond free tier | — | ~$0.00002400/vCPU-sec |

> Cloud Run scales to zero when not in use — ideal for demo/hackathon workloads.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `PORT` binding error | Ensure CMD uses `${PORT:-8080}` not a hardcoded port |
| Image too large | Add more exclusions to `.dockerignore` |
| SQLite in production | Replace with Cloud SQL (PostgreSQL) for persistent storage |
| Cold start delays | Set `--min-instances 1` to keep one instance warm |
| Auth errors (LLM) | Set `MOCK_MODE=false` and inject credentials via Secret Manager |

---

*Generated: 2026-02-28 · VelocityHire v5.0 · Containerisation Guide*
