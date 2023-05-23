# Cloud Build Trigger

gcloud builds submit \
--substitutions=_GCP_PROJECT_ID="$GCP_PROJECT_ID",_GCP_REGION="$GCP_REGION",_ARTIFACT_REPO_NAME="$ARTIFACT_REPO_NAME",_IMAGE_NAME="$APP_NAME" \
--region=$GCP_REGION \
--config cloudbuild.yaml
