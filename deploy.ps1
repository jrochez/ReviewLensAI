#Requires -Version 5.1
<#
.SYNOPSIS
    Full deployment of ReviewLensAI to Google Cloud Run.
    Requires: gcloud CLI authenticated, Docker, project 'reviewlensai' exists.
#>
$ErrorActionPreference = "Stop"

$PROJECT      = "reviewlensai"
$REGION       = "us-central1"
$REGISTRY     = "us-central1-docker.pkg.dev/$PROJECT/reviewlensai"
$BACKEND_IMG  = "$REGISTRY/backend:latest"
$FRONTEND_IMG = "$REGISTRY/frontend:latest"
$BUCKET       = "reviewlensai-data"
$DOMAIN       = "reviewlens.rochez.net"
$BACKEND_SVC  = "reviewlens-backend"
$FRONTEND_SVC = "reviewlens-frontend"

function Write-Step([string]$Msg) {
    Write-Host "`n=== $Msg ===" -ForegroundColor Cyan
}

# ── Enable APIs ───────────────────────────────────────────────────────────────
Write-Step "Enabling required APIs"
gcloud services enable `
    run.googleapis.com `
    secretmanager.googleapis.com `
    artifactregistry.googleapis.com `
    cloudbuild.googleapis.com `
    storage.googleapis.com `
    --project=$PROJECT

# ── Artifact Registry ────────────────────────────────────────────────────────
Write-Step "Creating Artifact Registry repository"
$null = gcloud artifacts repositories create reviewlensai `
    --repository-format=docker `
    --location=$REGION `
    --project=$PROJECT 2>&1
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

# ── Read secrets from .env ────────────────────────────────────────────────────
Write-Step "Reading secret values from .env"
$envVars = @{}
foreach ($line in (Get-Content ".env")) {
    if ($line -match "^([^#=\s][^=]*)=(.*)$") {
        $envVars[$Matches[1].Trim()] = $Matches[2].Trim()
    }
}

# ── Create Secrets in Secret Manager ─────────────────────────────────────────
Write-Step "Creating secrets in Secret Manager"
foreach ($secretName in @("OPENAI_API_KEY", "SECRET_KEY", "BRIGHTDATA_API_KEY", "BRIGHTDATA_DATASET_ID")) {
    $null = gcloud secrets create $secretName `
        --replication-policy=automatic `
        --project=$PROJECT 2>&1

    $val = $envVars[$secretName]
    if (-not $val) {
        Write-Error "ERROR: $secretName not found in .env"
        exit 1
    }
    $tmpFile = [System.IO.Path]::GetTempFileName()
    # Write without BOM, no trailing newline
    [System.IO.File]::WriteAllText($tmpFile, $val, (New-Object System.Text.UTF8Encoding $false))
    gcloud secrets versions add $secretName --data-file=$tmpFile --project=$PROJECT
    Remove-Item $tmpFile -Force
    Write-Host "  ✓ $secretName" -ForegroundColor Green
}

# ── GCS Data Bucket ───────────────────────────────────────────────────────────
Write-Step "Creating persistent data bucket: gs://$BUCKET"
$null = gcloud storage buckets create "gs://$BUCKET" `
    --location=$REGION `
    --project=$PROJECT 2>&1
Write-Host "  ✓ gs://$BUCKET" -ForegroundColor Green

# ── IAM: grant Cloud Run default SA access to secrets and bucket ──────────────
Write-Step "Configuring IAM permissions"
$PROJECT_NUMBER = (gcloud projects describe $PROJECT --format="value(projectNumber)")
$CR_SA = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud projects add-iam-policy-binding $PROJECT `
    --member="serviceAccount:$CR_SA" `
    --role="roles/secretmanager.secretAccessor" `
    --condition=None | Out-Null

gcloud storage buckets add-iam-policy-binding "gs://$BUCKET" `
    --member="serviceAccount:$CR_SA" `
    --role="roles/storage.objectAdmin" | Out-Null

Write-Host "  ✓ Granted secretmanager.secretAccessor + storage.objectAdmin to $CR_SA" -ForegroundColor Green

# ── Build Backend Image ───────────────────────────────────────────────────────
Write-Step "Building backend image via Cloud Build"
gcloud builds submit `
    --config=cloudbuild-backend.yaml `
    "--substitutions=_IMAGE=$BACKEND_IMG" `
    --project=$PROJECT .

# ── Deploy Backend ────────────────────────────────────────────────────────────
Write-Step "Deploying backend Cloud Run service"
gcloud run deploy $BACKEND_SVC `
    --image=$BACKEND_IMG `
    --region=$REGION `
    --project=$PROJECT `
    --platform=managed `
    --allow-unauthenticated `
    --port=8080 `
    --execution-environment=gen2 `
    --memory=2Gi `
    --cpu=1 `
    --min-instances=0 `
    --max-instances=3 `
    --set-secrets="ADMIN_EMAIL=ADMIN_EMAIL:latest,ADMIN_PASSWORD=ADMIN_PASSWORD:latest,OPENAI_API_KEY=OPENAI_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest,BRIGHTDATA_API_KEY=BRIGHTDATA_API_KEY:latest,BRIGHTDATA_DATASET_ID=BRIGHTDATA_DATASET_ID:latest" `
    --set-env-vars="DATABASE_URL=sqlite+aiosqlite:////app/data/reviewlens.db,CHROMA_PERSIST_DIR=/app/data/chromadb,INJECTION_BLOCKLIST_PATH=/app/config/injection_blocklist.txt" `
    --add-volume="name=data,type=cloud-storage,bucket=$BUCKET" `
    --add-volume-mount="volume=data,mount-path=/app/data"

$BACKEND_URL = (gcloud run services describe $BACKEND_SVC `
    --region=$REGION --project=$PROJECT --format="value(status.url)")
Write-Host "  ✓ Backend URL: $BACKEND_URL" -ForegroundColor Green

# ── Build Frontend Image (bakes in backend URL) ───────────────────────────────
Write-Step "Building frontend image (BACKEND_URL=$BACKEND_URL)"
gcloud builds submit `
    --config=cloudbuild-frontend.yaml `
    "--substitutions=_IMAGE=$FRONTEND_IMG,_BACKEND_URL=$BACKEND_URL" `
    --project=$PROJECT .

# ── Deploy Frontend ───────────────────────────────────────────────────────────
Write-Step "Deploying frontend Cloud Run service"
gcloud run deploy $FRONTEND_SVC `
    --image=$FRONTEND_IMG `
    --region=$REGION `
    --project=$PROJECT `
    --platform=managed `
    --allow-unauthenticated `
    --port=8080 `
    --memory=512Mi `
    --cpu=1 `
    --min-instances=0 `
    --max-instances=3 `
    --set-env-vars="NODE_ENV=production,HOSTNAME=0.0.0.0,PORT=8080"

$FRONTEND_URL = (gcloud run services describe $FRONTEND_SVC `
    --region=$REGION --project=$PROJECT --format="value(status.url)")
Write-Host "  ✓ Frontend URL: $FRONTEND_URL" -ForegroundColor Green

# ── Domain Mapping + SSL ──────────────────────────────────────────────────────
Write-Step "Creating domain mapping for $DOMAIN"
Write-Host ""
Write-Host "NOTE: If prompted about domain ownership verification, you must add" -ForegroundColor Yellow
Write-Host "a TXT record to rochez.net DNS before this step succeeds." -ForegroundColor Yellow
Write-Host "See: https://search.google.com/search-console" -ForegroundColor Yellow
Write-Host ""

gcloud run domain-mappings create `
    --service=$FRONTEND_SVC `
    --domain=$DOMAIN `
    --region=$REGION `
    --project=$PROJECT

# ── Print DNS Records ─────────────────────────────────────────────────────────
Write-Step "DNS records for $DOMAIN"
Write-Host "(Add these at your DNS registrar for rochez.net)" -ForegroundColor Yellow
Write-Host ""

$records = gcloud run domain-mappings describe `
    --domain=$DOMAIN `
    --region=$REGION `
    --project=$PROJECT `
    --format="value(status.resourceRecords)"

Write-Host $records

Write-Host ""
Write-Host "Standard Cloud Run Domain Mapping IPs (if not shown above):" -ForegroundColor Yellow
Write-Host "  A records:    216.239.32.21, 216.239.34.21, 216.239.36.21, 216.239.38.21"
Write-Host "  AAAA records: 2001:4860:4802:32::15, 2001:4860:4802:34::15"
Write-Host "                2001:4860:4802:36::15, 2001:4860:4802:38::15"
Write-Host ""
Write-Host "=== Deployment Complete ===" -ForegroundColor Green
Write-Host "  App URL:     https://$DOMAIN  (live after DNS propagation + SSL provisioning)"
Write-Host "  Backend:     $BACKEND_URL"
Write-Host "  Frontend:    $FRONTEND_URL"
Write-Host ""
Write-Host "SSL certificate auto-provisions once DNS records are live." -ForegroundColor Yellow
