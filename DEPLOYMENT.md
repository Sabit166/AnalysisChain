# Deployment Guide

This guide covers deploying AnalysisChain in various environments.

## Local Development

### Windows

```powershell
# Setup
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m src.cli new-session
```

### Linux/Mac

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m src.cli new-session
```

## Production Deployment

### Option 1: Package Installation

```bash
# Install as package
pip install -e .

# Now you can use the command directly
analysischain new-session
analysischain query SESSION_ID "Your question"
```

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY src/ ./src/
COPY setup.py .

# Install application
RUN pip install -e .

# Create data directories
RUN mkdir -p /app/data/vectordb /app/data/sessions /app/logs

# Environment variables will be provided at runtime
ENV PYTHONUNBUFFERED=1

ENTRYPOINT ["python", "-m", "src.cli"]
```

Build and run:

```bash
# Build image
docker build -t analysischain:latest .

# Run with environment file
docker run --rm \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  analysischain:latest new-session
```

### Option 3: Cloud Deployment

#### AWS EC2

```bash
# Install on EC2 instance
sudo apt-get update
sudo apt-get install python3.11 python3-pip python3-venv

# Clone and setup
git clone https://github.com/yourusername/AnalysisChain.git
cd AnalysisChain
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure with AWS Secrets Manager
aws secretsmanager get-secret-value \
  --secret-id analysischain/api-keys \
  --query SecretString \
  --output text > .env

# Run as systemd service (see below)
```

#### Google Cloud Platform

```bash
# Deploy to Cloud Run
gcloud run deploy analysischain \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
```

#### Azure

```bash
# Deploy to Azure Container Instances
az container create \
  --resource-group myResourceGroup \
  --name analysischain \
  --image analysischain:latest \
  --environment-variables \
    ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY} \
  --restart-policy OnFailure
```

## Service Configuration

### Systemd Service (Linux)

Create `/etc/systemd/system/analysischain.service`:

```ini
[Unit]
Description=AnalysisChain Agent Service
After=network.target

[Service]
Type=simple
User=analysischain
WorkingDirectory=/opt/analysischain
Environment="PATH=/opt/analysischain/venv/bin"
EnvironmentFile=/opt/analysischain/.env
ExecStart=/opt/analysischain/venv/bin/python -m src.cli
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable analysischain
sudo systemctl start analysischain
sudo systemctl status analysischain
```

### Windows Service

Use `nssm` (Non-Sucking Service Manager):

```powershell
# Install nssm
choco install nssm

# Install service
nssm install AnalysisChain "C:\AnalysisChain\venv\Scripts\python.exe" "-m src.cli"
nssm set AnalysisChain AppDirectory "C:\AnalysisChain"
nssm set AnalysisChain AppEnvironmentExtra "PATH=C:\AnalysisChain\venv\Scripts"

# Start service
nssm start AnalysisChain
```

## API Server Deployment

For REST API deployment, create `src/api_server.py`:

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.agent import AnalysisChainAgent

app = FastAPI()

class QueryRequest(BaseModel):
    session_id: str
    query: str
    use_rag: bool = True
    use_cache: bool = True

@app.post("/query")
async def process_query(request: QueryRequest):
    try:
        agent = AnalysisChainAgent(session_id=request.session_id)
        response, metadata = agent.process_query(
            query=request.query,
            use_rag=request.use_rag,
            use_cache=request.use_cache
        )
        return {"response": response, "metadata": metadata}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

Deploy with Gunicorn:

```bash
# Install FastAPI and Gunicorn
pip install fastapi uvicorn gunicorn

# Run
gunicorn src.api_server:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

## Environment-Specific Configurations

### Development

```env
LOG_LEVEL=DEBUG
CLAUDE_MAX_TOKENS=4096
CHUNK_SIZE=500
MAX_SESSION_AGE=3600
```

### Staging

```env
LOG_LEVEL=INFO
CLAUDE_MAX_TOKENS=8192
CHUNK_SIZE=1000
MAX_SESSION_AGE=7200
```

### Production

```env
LOG_LEVEL=WARNING
CLAUDE_MAX_TOKENS=8192
CHUNK_SIZE=1500
MAX_SESSION_AGE=86400
```

## Monitoring

### Logging

Configure centralized logging:

```python
# src/logging_config.py
import logging
from logging.handlers import SysLogHandler

handler = SysLogHandler(address=('logs.example.com', 514))
logger.addHandler(handler)
```

### Metrics

Track key metrics:

```python
# Track token usage
total_tokens = sum(
    metadata['usage']['input_tokens'] 
    for _, metadata in results
)

# Track cache efficiency
cache_hit_rate = metadata['cache_info']['cache_hit_rate']

# Track latency
import time
start = time.time()
response, metadata = agent.process_query(query)
latency = time.time() - start
```

## Scaling

### Horizontal Scaling

Use Redis for shared session state:

```python
# Install: pip install redis
import redis
from src.session_manager import SessionManager

class RedisSessionManager(SessionManager):
    def __init__(self):
        self.redis_client = redis.Redis(
            host='localhost',
            port=6379,
            decode_responses=True
        )
```

### Load Balancing

Use Nginx:

```nginx
upstream analysischain {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}

server {
    listen 80;
    location / {
        proxy_pass http://analysischain;
    }
}
```

## Security

### API Key Management

```bash
# Use environment variables
export ANTHROPIC_API_KEY=$(cat /secure/path/api_key)

# Or use secrets manager
aws secretsmanager get-secret-value \
  --secret-id prod/analysischain/api-keys
```

### Access Control

```python
# Add authentication middleware
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def verify_token(credentials = Depends(security)):
    if credentials.credentials != expected_token:
        raise HTTPException(status_code=403)
```

## Backup and Recovery

### Backup Vector Database

```bash
# Backup
tar -czf vectordb_backup_$(date +%Y%m%d).tar.gz data/vectordb/

# Restore
tar -xzf vectordb_backup_20240101.tar.gz -C data/
```

### Backup Sessions

```bash
# Regular backups
0 2 * * * tar -czf /backups/sessions_$(date +\%Y\%m\%d).tar.gz /app/data/sessions/
```

## Troubleshooting

### High Memory Usage

```bash
# Reduce chunk size
CHUNK_SIZE=500

# Limit concurrent operations
MAX_WORKERS=2
```

### Slow Performance

```bash
# Use faster embedding model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Reduce RAG chunks
--chunks 3
```

### Connection Issues

```bash
# Increase timeout
TIMEOUT=120

# Add retry logic
MAX_RETRIES=5
```

## Maintenance

### Regular Tasks

```bash
# Weekly: Cleanup expired sessions
0 0 * * 0 python -m src.cli cleanup

# Monthly: Backup data
0 0 1 * * /scripts/backup.sh

# Daily: Rotate logs
0 0 * * * /usr/sbin/logrotate /etc/logrotate.d/analysischain
```

### Updates

```bash
# Update dependencies
git pull
pip install -r requirements.txt --upgrade

# Restart service
sudo systemctl restart analysischain
```

## Health Checks

```python
# Add health endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }
```

## Support

For deployment issues:
1. Check logs: `tail -f logs/agent.log`
2. Verify configuration: `cat .env`
3. Test connectivity: `python -m src.cli info`
4. Open GitHub issue with deployment details
