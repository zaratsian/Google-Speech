gcloud services enable \
drive.googleapis.com \
docs.googleapis.com \
people.googleapis.com

# Create Google Cloud Artifact Repo
gcloud artifacts repositories create $ARTIFACT_REPO_NAME \
--location=$GCP_REGION \
--description="STT Repo" \
--repository-format=docker
