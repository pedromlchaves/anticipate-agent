#!/bin/sh

REQUIRED_VARS="GOOGLE_GENAI_USE_VERTEXAI MAPS_API_KEY GOOGLE_CLOUD_PROJECT GOOGLE_CLOUD_LOCATION LANGFUSE_SECRET_KEY LANGFUSE_PUBLIC_KEY LANGFUSE_HOST"
MISSING=0
echo "[ENTRYPOINT] Checking required environment variables..."
for VAR in $REQUIRED_VARS; do
  if [ -z "$(eval echo \"\$$VAR\")" ]; then
    echo "[ERROR] Environment variable $VAR is not set!"
    MISSING=1
  else
    echo "[OK] $VAR is set: $(eval echo \"\$$VAR\")"
  fi
done
if [ $MISSING -eq 1 ]; then
  echo "[ENTRYPOINT] One or more required environment variables are missing. Exiting."
  exit 1
fi
echo "[ENTRYPOINT] All required environment variables are set. Starting application..."
exec "$@"
