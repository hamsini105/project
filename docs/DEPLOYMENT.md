# Deployment Guide

## Prerequisites

- Docker ≥ 24 and Docker Compose v2 (for containerised deployment)
- Python 3.10–3.12 (for non-Docker deployment)
- 4 GB RAM minimum (sentence-transformers loads ~500 MB model weights)

---

## Local Development (non-Docker)

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
streamlit run app.py
```

The dashboard is served at **http://localhost:8501**.

---

## Docker — Development

The development stage mounts your local source directory so code changes are reflected without rebuilding the image.

```bash
docker compose up app
```

Streamlit's hot-reload watches for file changes automatically.  Press `Ctrl+C` to stop.

---

## Docker — Production

The production stage:
- Runs as a non-root user (`appuser`)
- Pre-downloads the embedding model into the image
- Sets XSRF protection and disables CORS
- Includes a health check on `/_stcore/health`

```bash
docker compose --profile production up app-prod
```

To build and tag manually:

```bash
docker build --target production -t resume-parser-system:1.3.0 .
docker run -p 8501:8501 \
  -e ENVIRONMENT=production \
  -e LOG_FORMAT=json \
  resume-parser-system:1.3.0
```

---

## Environment Variables

All variables are read from the environment or from `.env` (development only — never commit `.env` to source control).

| Variable | Required | Default | Notes |
|---|---|---|---|
| `ENVIRONMENT` | No | `development` | Set to `production` in live environments |
| `DEBUG` | No | `false` | Never set to `true` in production |
| `LOG_LEVEL` | No | `INFO` | Use `DEBUG` only for troubleshooting |
| `LOG_FORMAT` | No | `text` | Set to `json` for Datadog / CloudWatch / Loki |
| `LOG_FILE` | No | _(stdout)_ | Path for a rotating log file |
| `MAX_UPLOAD_SIZE_MB` | No | `10` | Must match `SERVER_MAX_UPLOAD_MB` |
| `EMBEDDING_MODEL_NAME` | No | `all-MiniLM-L6-v2` | Must be a valid Sentence Transformers model ID |
| `EMBEDDING_CACHE_SIZE` | No | `1024` | Increase for high-concurrency deployments |
| `SERVER_PORT` | No | `8501` | Must match the container port mapping |

---

## Health Check

The Streamlit server exposes a health endpoint:

```
GET /_stcore/health
→ 200 OK  (server is ready)
```

The Docker `HEALTHCHECK` directive uses this endpoint.  External load balancers or orchestrators (ECS, Kubernetes) should target this path.

---

## Cloud Deployment (AWS ECS example)

1. Build and push the production image to ECR:

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com

docker build --target production -t resume-parser-system:latest .
docker tag  resume-parser-system:latest <account>.dkr.ecr.us-east-1.amazonaws.com/resume-parser-system:latest
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/resume-parser-system:latest
```

2. Create an ECS task definition with:
   - CPU: 1 vCPU, Memory: 4 GB (minimum)
   - Container port: 8501
   - Environment variables from AWS Secrets Manager or Parameter Store
   - Health check: `/_stcore/health`

3. Place behind an Application Load Balancer with a target group on port 8501.

---

## Performance Notes

- **Embedding model cold start**: The sentence-transformers model is pre-loaded in the production Docker image.  On first request after container restart, the model is loaded from disk (~2–5 seconds).  Use a warm-up script or keep at least one container always running.
- **Embedding cache**: The in-process LRU cache (`EMBEDDING_CACHE_SIZE`) avoids re-encoding repeated texts.  Set this to roughly 2× the number of unique job descriptions you expect per hour.
- **Streamlit reruns**: Streamlit reruns the entire script on every user interaction.  All heavy operations (data loading, model loading) are cached with `@st.cache_data` or `@st.cache_resource`.

---

## Security Checklist

- [ ] `.env` is excluded from source control (`.gitignore`)
- [ ] `ENVIRONMENT=production` is set
- [ ] `DEBUG=false` is set
- [ ] `SERVER_ENABLE_XSRF=true` is set
- [ ] Container runs as non-root user (`appuser`)
- [ ] No secrets are baked into the Docker image
- [ ] Uploaded file size is restricted (`MAX_UPLOAD_SIZE_MB`)
- [ ] `LOG_FORMAT=json` for structured log aggregation
