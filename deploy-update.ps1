#Requires -Version 5.1
<#
.SYNOPSIS
    Rebuild and redeploy ReviewLensAI containers to existing Cloud Run services.
    Assumes: Artifact Registry repo, secrets, bucket, IAM, and domain mapping already exist.
#>
$ErrorActionPreference = "Stop"

$PROJECT      = "reviewlensai"
$REGION       = "us-central1"
$REGISTRY     = "us-central1-docker.pkg.dev/$PROJECT/reviewlensai"
$BACKEND_IMG  = "$REGISTRY/backend:latest"
$FRONTEND_IMG = "$REGISTRY/frontend:latest"
$BACKEND_SVC  = "reviewlens-backend"
$FRONTEND_SVC = "reviewlens-frontend"

function Write-Step([string]$Msg) {
    Write-Host "`n=== $Msg ===" -ForegroundColor Cyan
}

# ── Build and deploy backend ──────────────────────────────────────────────────
Write-Step "Building backend image"
gcloud builds submit `
    --config=cloudbuild-backend.yaml `
    "--substitutions=_IMAGE=$BACKEND_IMG" `
    --project=$PROJECT .

Write-Step "Deploying backend"
gcloud run deploy $BACKEND_SVC `
    --image=$BACKEND_IMG `
    --region=$REGION `
    --project=$PROJECT `
    --platform=managed

$BACKEND_URL = (gcloud run services describe $BACKEND_SVC `
    --region=$REGION --project=$PROJECT --format="value(status.url)")
Write-Host "  ✓ Backend URL: $BACKEND_URL" -ForegroundColor Green

# ── Build and deploy frontend (bakes in current backend URL) ──────────────────
Write-Step "Building frontend image (BACKEND_URL=$BACKEND_URL)"
gcloud builds submit `
    --config=cloudbuild-frontend.yaml `
    "--substitutions=_IMAGE=$FRONTEND_IMG,_BACKEND_URL=$BACKEND_URL" `
    --project=$PROJECT .

Write-Step "Deploying frontend"
gcloud run deploy $FRONTEND_SVC `
    --image=$FRONTEND_IMG `
    --region=$REGION `
    --project=$PROJECT `
    --platform=managed

Write-Host "`n=== Done ===" -ForegroundColor Green
Write-Host "  https://reviewlens.rochez.net"
