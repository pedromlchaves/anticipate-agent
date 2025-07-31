

echo "\033[1;34m[INFO]\033[0m Checking required environment variables..."
REQUIRED_VARS=(GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION GOOGLE_GENAI_USE_VERTEXAI MAPS_API_KEY)
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    # Try to source .env if it exists and variable is still not set
    if [ -f driver-assistant/.env ]; then
      set -a
      . driver-assistant/.env
      set +a
    fi
    if [ -z "${!VAR}" ]; then
      echo "\033[1;33m[WARN]\033[0m $VAR is not set."
      read -p "Enter value for $VAR: " $VAR
      export $VAR
      echo "\033[1;32m[SET]\033[0m $VAR set."
    else
      echo "\033[1;32m[OK]\033[0m $VAR loaded from .env."
    fi
  else
    echo "\033[1;32m[OK]\033[0m $VAR is set."
  fi
done

echo "\033[1;34m[INFO]\033[0m All required environment variables are set."
echo "\033[1;34m[INFO]\033[0m Deploying to Google Cloud Run..."

gcloud run deploy driver-assistant-service \
--source . \
--region $GOOGLE_CLOUD_LOCATION \
--project $GOOGLE_CLOUD_PROJECT \
--allow-unauthenticated \
--set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT,GOOGLE_CLOUD_LOCATION=$GOOGLE_CLOUD_LOCATION,GOOGLE_GENAI_USE_VERTEXAI=$GOOGLE_GENAI_USE_VERTEXAI,MAPS_API_KEY=$MAPS_API_KEY" \
--memory=2Gi \
--cpu=2 \


if [ $? -eq 0 ]; then
  echo "\033[1;32m[SUCCESS]\033[0m Deployment completed successfully!"
else
  echo "\033[1;31m[ERROR]\033[0m Deployment failed. Please check the logs above."
fi