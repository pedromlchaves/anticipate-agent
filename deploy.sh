

echo "\033[1;34m[INFO]\033[0m Checking required environment variables..."
REQUIRED_VARS=(GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION GOOGLE_GENAI_USE_VERTEXAI MAPS_API_KEY)
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo "\033[1;33m[WARN]\033[0m $VAR is not set."
    read -p "Enter value for $VAR: " $VAR
    export $VAR
    echo "\033[1;32m[SET]\033[0m $VAR set."
  else
    echo "\033[1;32m[OK]\033[0m $VAR is set."
  fi
done

echo "\033[1;34m[INFO]\033[0m All required environment variables are set."
echo "\033[1;34m[INFO]\033[0m Deploying to Google Cloud Run..."