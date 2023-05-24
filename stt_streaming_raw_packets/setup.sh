# Enable Google Cloud APIs
gcloud services enable \
artifactregistry.googleapis.com \
container.googleapis.com \
cloudbuild.googleapis.com

# Create Google Cloud Artifact Repo
gcloud artifacts repositories create $ARTIFACT_REPO_NAME \
--location=$GCP_REGION \
--description="STT Repo" \
--repository-format=docker

# Create GKE Autopilot Cluster
gcloud container clusters create-auto $GKE_CLUSTER_NAME \
    --region $GCP_REGION \
    --project=$GCP_PROJECT_ID

