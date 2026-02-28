#!/usr/bin/env bash
# setup-wif.sh — Configure Workload Identity Federation for GitHub Actions → Google Cloud Run
#
# Usage:
#   export GCP_PROJECT_ID=my-project-id
#   export GCP_REGION=us-central1           # optional, default: us-central1
#   bash scripts/setup-wif.sh
#
# After this script completes, add the printed values as GitHub Actions secrets:
#   Settings → Secrets and variables → Actions → New repository secret

set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
PROJECT_ID="${GCP_PROJECT_ID:?Set GCP_PROJECT_ID before running this script}"
REGION="${GCP_REGION:-us-central1}"
GITHUB_REPO="agentic-wq/velocityhire"
POOL_ID="github-pool"
PROVIDER_ID="github-provider"
SA_NAME="velocityhire-deploy"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  VelocityHire — Workload Identity Federation setup"
echo "  Project : ${PROJECT_ID}"
echo "  Region  : ${REGION}"
echo "  Repo    : ${GITHUB_REPO}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Enable required APIs ────────────────────────────────────────────────────
echo ""
echo "1/6  Enabling required GCP APIs…"
gcloud services enable \
  iamcredentials.googleapis.com \
  cloudresourcemanager.googleapis.com \
  run.googleapis.com \
  artifactregistry.googleapis.com \
  --project="${PROJECT_ID}" --quiet

# ── 2. Create a dedicated deployment service account ──────────────────────────
echo ""
echo "2/6  Creating service account ${SA_EMAIL}…"
if gcloud iam service-accounts describe "${SA_EMAIL}" \
     --project="${PROJECT_ID}" --quiet 2>/dev/null; then
  echo "     (already exists — skipping creation)"
else
  gcloud iam service-accounts create "${SA_NAME}" \
    --display-name="VelocityHire GitHub Actions deployer" \
    --project="${PROJECT_ID}" --quiet
fi

# Grant only the permissions needed to push images and deploy to Cloud Run
for ROLE in \
  roles/artifactregistry.writer \
  roles/run.admin \
  roles/iam.serviceAccountUser; do
  gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="${ROLE}" \
    --condition=None \
    --quiet
done

# ── 3. Create the Workload Identity Pool ──────────────────────────────────────
echo ""
echo "3/6  Creating Workload Identity Pool '${POOL_ID}'…"
if gcloud iam workload-identity-pools describe "${POOL_ID}" \
     --location=global --project="${PROJECT_ID}" --quiet 2>/dev/null; then
  echo "     (already exists — skipping creation)"
else
  gcloud iam workload-identity-pools create "${POOL_ID}" \
    --location=global \
    --display-name="GitHub Actions pool" \
    --project="${PROJECT_ID}" --quiet
fi

POOL_RESOURCE=$(gcloud iam workload-identity-pools describe "${POOL_ID}" \
  --location=global --project="${PROJECT_ID}" \
  --format="value(name)")

# ── 4. Create the GitHub OIDC provider ────────────────────────────────────────
echo ""
echo "4/6  Creating OIDC provider '${PROVIDER_ID}' in pool '${POOL_ID}'…"
if gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
     --workload-identity-pool="${POOL_ID}" \
     --location=global --project="${PROJECT_ID}" --quiet 2>/dev/null; then
  echo "     (already exists — skipping creation)"
else
  gcloud iam workload-identity-pools providers create-oidc "${PROVIDER_ID}" \
    --workload-identity-pool="${POOL_ID}" \
    --location=global \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --attribute-condition="attribute.repository == '${GITHUB_REPO}'" \
    --project="${PROJECT_ID}" --quiet
fi

PROVIDER_RESOURCE=$(gcloud iam workload-identity-pools providers describe "${PROVIDER_ID}" \
  --workload-identity-pool="${POOL_ID}" \
  --location=global --project="${PROJECT_ID}" \
  --format="value(name)")

# ── 5. Bind the service account to the WIF pool ───────────────────────────────
echo ""
echo "5/6  Binding service account to WIF pool…"
gcloud iam service-accounts add-iam-policy-binding "${SA_EMAIL}" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_RESOURCE}/attribute.repository/${GITHUB_REPO}" \
  --quiet

# ── 6. Print GitHub secret values ─────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  6/6  Done! Add these as GitHub Actions secrets:"
echo "       Settings → Secrets and variables → Actions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  GCP_PROJECT_ID"
echo "    ${PROJECT_ID}"
echo ""
echo "  GCP_REGION  (optional — defaults to us-central1)"
echo "    ${REGION}"
echo ""
echo "  GCP_SERVICE_ACCOUNT"
echo "    ${SA_EMAIL}"
echo ""
echo "  GCP_WORKLOAD_IDENTITY_PROVIDER"
echo "    ${PROVIDER_RESOURCE}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
