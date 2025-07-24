# Ride-O-Clock Agent

This repository contains a Google ADK-based agent designed to run locally for development or be deployed to Google Cloud Run. The agent provides intelligent driver assistance and routing capabilities using Google Maps, weather, and transportation APIs.

## Features
- Google ADK agent for driver assistance
- Local development with Docker
- Cloud deployment via Google Cloud Run
- Integrates with Google Maps, weather, and transportation APIs
- FastAPI web server

## Requirements
- Python 3.13 (Dockerized)
- Google Cloud SDK (`gcloud` CLI)
- Docker
- Google Cloud project with required APIs enabled

## Setup

### 1. Local Development

#### Prerequisites
- Install [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)
- Install [Docker](https://docs.docker.com/get-docker/)
- Authenticate with Google Cloud:
  ```sh
  gcloud auth login
  gcloud auth application-default login
  ```

#### Run Locally
Use the provided script to build and run the agent in Docker:

```sh
./run-local.sh
```

This will:
- Check for `gcloud` and authentication
- Build the Docker image
- Start the container with Google Cloud credentials mounted
- Expose the service at [http://localhost:8080](http://localhost:8080)

**Stop the service:**
```sh
docker stop driver-assistant-local
```
**View logs:**
```sh
docker logs -f driver-assistant-local
```

### 2. Deploy to Google Cloud Run

#### Prerequisites
- Set environment variables:
  - `GOOGLE_CLOUD_PROJECT`: Your GCP project ID
  - `GOOGLE_CLOUD_LOCATION`: Deployment region (e.g., `us-central1`)
  - `GOOGLE_GENAI_USE_VERTEXAI`: Set if using Vertex AI
  - `MAPS_API_KEY`: Your Google Maps API key

#### Deploy
Use the provided script:

```sh
./deploy.sh
```

This will:
- Deploy the agent to Cloud Run
- Set required environment variables
- Allow unauthenticated access

## Project Structure
- `main.py`: FastAPI entrypoint using Google ADK
- `driver-assistant/`: Agent code, tools, and utilities
- `requirements.txt`: Python dependencies
- `Dockerfile`: Container build instructions
- `run-local.sh`: Local development script
- `deploy.sh`: Cloud Run deployment script

## Dependencies
See `requirements.txt` for all Python packages used, including:
- `google_adk`
- `requests`, `bs4`, `selenium`, `pandas`
- `googlemaps`, `google-maps-routing`, `google-api-python-client`
- `grpcio`, `protobuf`, `deprecated`

## Usage
- Local: [http://localhost:8080](http://localhost:8080)
- Cloud Run: Service URL provided after deployment

## License
MIT
