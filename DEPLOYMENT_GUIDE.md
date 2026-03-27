# Production Deployment Guide - Compliance Autopilot

This guide covers deploying the Compliance Autopilot dashboard to production for public access.

## Quick Start - Docker Deployment (Recommended)

### 1. Create Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Environment variables
ENV DATABASE_URL=sqlite:///data/compliance_autopilot.db
ENV HOST=0.0.0.0
ENV PORT=8000

# Expose port
EXPOSE 8000

# Initialize database and start server
CMD python3 -c "from app.models.database import init_db; init_db()" && \
    python3 -c "from app.scripts.seed_historic_circulars import seed_historic_circulars; seed_historic_circulars()" && \
    uvicorn main:app --host 0.0.0.0 --port 8000
```

### 2. Create docker-compose.yml

```yaml
version: '3.8'

services:
  compliance-autopilot:
    build: .
    container_name: compliance-dashboard
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///data/compliance_autopilot.db
      - HOST=0.0.0.0
      - PORT=8000
    restart: unless-stopped
```

### 3. Deploy with Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Cloud Deployment Options

### Option 1: Deploy to AWS (EC2)

```bash
# 1. Launch EC2 instance (t3.medium recommended)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-ec2-ip

# 3. Install Docker
sudo apt update
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# 4. Clone and deploy
git clone <your-repo>
cd compliance-autopilot
docker-compose up -d

# 5. Configure Security Group to allow port 8000
# Or use nginx reverse proxy for port 80/443
```

### Option 2: Deploy to Railway/Render/Fly.io (Easiest)

**Railway (Free tier available):**
1. Push code to GitHub
2. Connect Railway to GitHub repo
3. Set environment variables in Railway dashboard
4. Railway auto-deploys and provides public URL

**Render:**
1. Create `render.yaml`:
```yaml
services:
  - type: web
    name: compliance-autopilot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        value: sqlite:///data/compliance.db
```

### Option 3: Deploy to Google Cloud Run

```bash
# Build container
gcloud builds submit --tag gcr.io/PROJECT_ID/compliance-autopilot

# Deploy to Cloud Run
gcloud run deploy compliance-autopilot \
  --image gcr.io/PROJECT_ID/compliance-autopilot \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="DATABASE_URL=sqlite:///tmp/compliance.db"
```

---

## Production Configuration

### 1. Environment Variables (.env file)

```bash
# .env
DATABASE_URL=sqlite:///data/compliance_autopilot.db
HOST=0.0.0.0
PORT=8000
DEBUG=false

# Optional: Email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
NOTIFICATION_EMAILS=admin@company.com,compliance@company.com

# Optional: External services
OPENAI_API_KEY=sk-...  # For AI-powered analysis
```

### 2. Using PostgreSQL (Recommended for Production)

Update `requirements.txt`:
```
psycopg2-binary
```

Update `app/models/database.py`:
```python
import os
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///compliance_autopilot.db")
engine = create_engine(DATABASE_URL)
```

Update `docker-compose.yml`:
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: compliance
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: securepassword
    volumes:
      - postgres_data:/var/lib/postgresql/data

  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://admin:securepassword@db:5432/compliance
    depends_on:
      - db
    restart: unless-stopped

volumes:
  postgres_data:
```

---

## Setting Up HTTPS with Nginx

### 1. Install Nginx

```bash
sudo apt install -y nginx certbot python3-certbot-nginx
```

### 2. Create Nginx Config

```nginx
# /etc/nginx/sites-available/compliance-dashboard
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### 3. Enable HTTPS

```bash
sudo ln -s /etc/nginx/sites-available/compliance-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com
```

---

## Production Checklist

- [ ] Use PostgreSQL instead of SQLite for concurrent access
- [ ] Set up regular database backups
- [ ] Configure environment variables securely
- [ ] Enable HTTPS with SSL certificate
- [ ] Set up monitoring (UptimeRobot, Pingdom)
- [ ] Configure firewall rules (only allow 80, 443, 22)
- [ ] Enable automatic security updates
- [ ] Set up log rotation
- [ ] Configure SMTP for email notifications
- [ ] Add authentication if needed (see below)

---

## Adding Authentication (Optional)

For a public dashboard, you may want to add simple authentication:

### 1. Install dependencies

```bash
pip install python-jose passlib[bcrypt]
```

### 2. Add auth middleware to `main.py`

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets

security = HTTPBasic()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, "your-secure-password")
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Protect routes
@app.get("/api/dashboard/summary", dependencies=[Depends(verify_credentials)])
def get_dashboard_summary(db: Session = Depends(get_db)):
    ...
```

---

## Monitoring & Maintenance

### Health Check Endpoint
```bash
curl https://your-domain.com/health
# Returns: {"status":"healthy","service":"Compliance Autopilot","version":"1.0.0"}
```

### Backup Database (SQLite)
```bash
# Automated backup script
#!/bin/bash
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp /app/data/compliance_autopilot.db "$BACKUP_DIR/compliance_$TIMESTAMP.db"
# Keep only last 30 days
find $BACKUP_DIR -name "compliance_*.db" -mtime +30 -delete
```

### Log Monitoring
```bash
# View logs
docker-compose logs -f --tail 100

# Or with journald
sudo journalctl -u compliance-autopilot -f
```

---

## Estimated Costs

| Platform | Monthly Cost | Best For |
|----------|-------------|----------|
| Railway | $0-5 | Quick prototyping |
| Render | $0-7 | Small teams |
| AWS EC2 t3.micro | $8-15 | Full control |
| AWS EC2 t3.small | $15-30 | Production |
| Google Cloud Run | $0-10 | Variable traffic |
| DigitalOcean Droplet | $6-12 | Simple hosting |

---

## Troubleshooting

**Port already in use:**
```bash
sudo lsof -i :8000
sudo kill -9 <PID>
```

**Database locked (SQLite):**
- Switch to PostgreSQL for production
- Or ensure single process access

**Permission denied:**
```bash
sudo chown -R $USER:$USER /app/data
chmod 755 /app/data
```

---

## Next Steps

1. Choose your deployment platform
2. Set up domain name (optional but recommended)
3. Configure SSL/HTTPS
4. Set up monitoring alerts
5. Regular database backups

Your compliance dashboard will be accessible at `https://your-domain.com` or the provided cloud URL.