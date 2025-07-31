#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color


echo -e "${GREEN}🚀 Starting local development setup...${NC}"

# Step 0: Check required environment variables and prompt if missing
REQUIRED_VARS=(MAPS_API_KEY)
echo -e "${YELLOW}🔎 Checking required environment variables...${NC}"
for VAR in "${REQUIRED_VARS[@]}"; do
  if [ -z "${!VAR}" ]; then
    echo -e "${YELLOW}⚠️  $VAR is not set.${NC}"
    read -p "Enter value for $VAR: " $VAR
    export $VAR
    echo -e "${GREEN}✅ $VAR set.${NC}"
  else
    echo -e "${GREEN}✅ $VAR is set.${NC}"
  fi
done
echo -e "${GREEN}✅ All required environment variables are set.${NC}"

# Step 1: Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

# Step 2: Check if already authenticated
echo -e "${YELLOW}🔐 Checking Google Cloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
    echo -e "${YELLOW}🔑 No active authentication found. Logging in...${NC}"
    gcloud auth login
else
    echo -e "${GREEN}✅ Already authenticated with Google Cloud${NC}"
fi

# Step 3: Generate Application Default Credentials
echo -e "${YELLOW}🔑 Setting up Application Default Credentials...${NC}"
ADC_PATH="/Users/pedro.chaves/.config/gcloud/application_default_credentials.json"

if [ ! -f "$ADC_PATH" ]; then
    echo -e "${YELLOW}📝 Creating Application Default Credentials...${NC}"
    gcloud auth application-default login
else
    echo -e "${GREEN}✅ Application Default Credentials already exist${NC}"
fi

# Step 4: Set project if needed
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
    echo -e "${YELLOW}⚙️  Setting default project...${NC}"
    gcloud config set project $(gcloud projects list --format="value(projectId)" | head -n1)
fi

# Step 5: Build Docker image
echo -e "${YELLOW}🔨 Building Docker image...${NC}"
docker build -t driver-assistant-local .

# Step 6: Stop and remove any existing containers
echo -e "${YELLOW}🛑 Stopping and removing existing containers...${NC}"
docker stop $(docker ps -q --filter ancestor=driver-assistant-local) 2>/dev/null || true
docker rm $(docker ps -aq --filter ancestor=driver-assistant-local) 2>/dev/null || true

# Also remove by name if it exists
docker stop driver-assistant-local 2>/dev/null || true
docker rm driver-assistant-local 2>/dev/null || true

# Step 7: Run the container with mounted credentials
echo -e "${GREEN}🚀 Starting Docker container with Google Cloud credentials...${NC}"
docker run \
    --name driver-assistant-local \
    -p 8080:8080 \
    -e GOOGLE_APPLICATION_CREDENTIALS=/tmp/keys/application_default_credentials.json \
    -v ${ADC_PATH}:/tmp/keys/application_default_credentials.json:ro \
  driver-assistant-local

# Step 8: Wait for container to start and check health
echo -e "${YELLOW}⏳ Waiting for service to start...${NC}"
sleep 5

# Check if container is running
if docker ps | grep -q "driver-assistant-local"; then
    echo -e "${GREEN}✅ Container is running successfully!${NC}"
    echo -e "${GREEN}🌐 Service available at: http://localhost:8080${NC}"
    echo -e "${YELLOW}📋 Container logs:${NC}"
    docker logs driver-assistant-local --tail 10
else
    echo -e "${RED}❌ Container failed to start. Checking logs...${NC}"
    docker logs driver-assistant-local
    exit 1
fi

echo -e "${GREEN}🎉 Setup complete! Your service is running at http://localhost:8080${NC}"
echo -e "${YELLOW}💡 To stop the service, run: docker stop driver-assistant-local${NC}"
echo -e "${YELLOW}💡 To view logs, run: docker logs -f driver-assistant-local${NC}"