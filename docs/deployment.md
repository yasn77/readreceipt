# Deployment Guide

This guide covers deploying Read Receipt to production environments, including Docker, Kubernetes, and traditional server deployments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Docker Deployment](#docker-deployment)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Traditional Server Deployment](#traditional-server-deployment)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [SSL/TLS Configuration](#ssltls-configuration)
- [Production Checklist](#production-checklist)
- [Monitoring Setup](#monitoring-setup)
- [Backup and Recovery](#backup-and-recovery)

## Overview

Read Receipt can be deployed in various environments:

- **Docker** - Containerised deployment for consistency
- **Kubernetes** - Orchestrated deployment for scalability
- **Traditional Server** - Direct deployment on VM or bare metal

**Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                      Production Environment                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌────────────┐ │
│  │   Browser    │     │   Browser    │     │   Admin    │ │
│  │  Extension   │     │  Extension   │     │  Dashboard │ │
│  └──────┬───────┘     └──────┬───────┘     └─────┬──────┘ │
│         │                    │                    │        │
│         └────────────────────┼────────────────────┘        │
│                              │                              │
│                    ┌─────────▼─────────┐                   │
│                    │  Load Balancer    │                   │
│                    │  (nginx/Cloudflare)│                  │
│                    └─────────┬─────────┘                   │
│                              │                              │
│              ┌───────────────┼───────────────┐             │
│              │               │               │             │
│      ┌───────▼───────┐ ┌────▼────┐ ┌───────▼───────┐     │
│      │  Flask App 1  │ │ Flask   │ │  Flask App N  │     │
│      │  (Container)  │ │ App 2   │ │  (Container)  │     │
│      └───────┬───────┘ └────┬────┘ └───────┬───────┘     │
│              │               │               │             │
│              └───────────────┼───────────────┘             │
│                              │                              │
│                    ┌─────────▼─────────┐                   │
│                    │   PostgreSQL      │                   │
│                    │   Database        │                   │
│                    └───────────────────┘                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required

- **Server** - Linux server (Ubuntu 20.04+ recommended)
- **Domain** - Domain name for SSL certificate
- **Database** - PostgreSQL 12+ server
- **SSL Certificate** - Let's Encrypt or commercial certificate

### Recommended

- **Container Runtime** - Docker 20+
- **Orchestration** - Kubernetes 1.24+ (for K8s deployment)
- **Reverse Proxy** - nginx or Cloudflare
- **Monitoring** - Prometheus, Grafana
- **CI/CD** - GitHub Actions, GitLab CI

## Docker Deployment

### Build Docker Image

Create a `Dockerfile` in the project root:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY migrations/ ./migrations/

# Copy admin dashboard (pre-built)
COPY admin-dashboard/dist/ ./static/

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/')"

# Run application
CMD ["python", "app.py"]
```

### Build and Run

```bash
# Build Docker image
docker build -t readreceipt:latest .

# Run container
docker run -d \
  --name readreceipt \
  -p 5000:5000 \
  -e ADMIN_TOKEN=your-secure-token \
  -e SQLALCHEMY_DATABASE_URI=postgresql://user:pass@host:5432/readreceipt \
  -e LOG_LEVEL=WARNING \
  -v $(pwd)/data:/app/data \
  --restart unless-stopped \
  readreceipt:latest
```

### Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ADMIN_TOKEN=${ADMIN_TOKEN}
      - SQLALCHEMY_DATABASE_URI=postgresql://postgres:${POSTGRES_PASSWORD}@db:5432/readreceipt
      - LOG_LEVEL=WARNING
    depends_on:
      db:
        condition: service_healthy
    restart: unless-stopped
    networks:
      - readreceipt-network

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=readreceipt
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped
    networks:
      - readreceipt-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped
    networks:
      - readreceipt-network

volumes:
  postgres-data:

networks:
  readreceipt-network:
    driver: bridge
```

### nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream readreceipt {
        server app:5000;
    }

    # Redirect HTTP to HTTPS
    server {
        listen 80;
        server_name readreceipt.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS server
    server {
        listen 443 ssl http2;
        server_name readreceipt.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;

        location / {
            proxy_pass http://readreceipt;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Static files
        location /static/ {
            proxy_pass http://readreceipt;
        }
    }
}
```

### Run with Docker Compose

```bash
# Set environment variables
export ADMIN_TOKEN=your-secure-token
export POSTGRES_PASSWORD=secure-db-password

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Kubernetes Deployment

### Helm Chart

The project includes a Helm chart in `helm/readreceipt/`.

### Install with Helm

```bash
# Add repository (if published)
helm repo add readreceipt https://your-chart-repo.com

# Update repo
helm repo update

# Install chart
helm install readreceipt ./helm/readreceipt \
  --namespace readreceipt \
  --create-namespace \
  --set adminToken=your-secure-token \
  --set postgresql.auth.password=secure-db-password \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=readreceipt.yourdomain.com \
  --set ingress.tls[0].secretName=readreceipt-tls \
  --set ingress.tls[0].hosts[0]=readreceipt.yourdomain.com
```

### Custom Values

Create `values-production.yaml`:

```yaml
replicaCount: 3

image:
  repository: ghcr.io/yasn77/readreceipt
  tag: v0.1.3
  pullPolicy: IfNotPresent

env:
  ADMIN_TOKEN: "your-secure-token"
  LOG_LEVEL: "WARNING"
  SQLALCHEMY_DATABASE_URI: "postgresql://user:pass@postgres-host:5432/readreceipt"

service:
  type: ClusterIP
  port: 80

ingress:
  enabled: true
  className: nginx
  annotations:
    kubernetes.io/tls-acme: "true"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
  hosts:
    - host: readreceipt.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: readreceipt-tls
      hosts:
        - readreceipt.yourdomain.com

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 128Mi

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 80

postgresql:
  enabled: true
  auth:
    password: "secure-db-password"
  primary:
    persistence:
      enabled: true
      size: 10Gi
```

### Deploy with Custom Values

```bash
helm install readreceipt ./helm/readreceipt \
  -f values-production.yaml \
  --namespace readreceipt \
  --create-namespace
```

### Manual Kubernetes Manifests

Create `k8s/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: readreceipt
  namespace: readreceipt
spec:
  replicas: 3
  selector:
    matchLabels:
      app: readreceipt
  template:
    metadata:
      labels:
        app: readreceipt
    spec:
      containers:
      - name: readreceipt
        image: ghcr.io/yasn77/readreceipt:v0.1.3
        ports:
        - containerPort: 5000
        env:
        - name: ADMIN_TOKEN
          valueFrom:
            secretKeyRef:
              name: readreceipt-secrets
              key: admin-token
        - name: SQLALCHEMY_DATABASE_URI
          valueFrom:
            secretKeyRef:
              name: readreceipt-secrets
              key: database-uri
        - name: LOG_LEVEL
          value: "WARNING"
        resources:
          limits:
            cpu: 500m
            memory: 512Mi
          requests:
            cpu: 100m
            memory: 128Mi
        livenessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 5
```

Create `k8s/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: readreceipt
  namespace: readreceipt
spec:
  selector:
    app: readreceipt
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
```

Create `k8s/secrets.yaml`:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: readreceipt-secrets
  namespace: readreceipt
type: Opaque
stringData:
  admin-token: "your-secure-token"
  database-uri: "postgresql://user:pass@host:5432/readreceipt"
```

### Apply Kubernetes Manifests

```bash
# Create namespace
kubectl create namespace readreceipt

# Create secrets
kubectl apply -f k8s/secrets.yaml

# Deploy application
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml

# Check status
kubectl get pods -n readreceipt
kubectl get svc -n readreceipt

# View logs
kubectl logs -f deployment/readreceipt -n readreceipt
```

## Traditional Server Deployment

### System Requirements

- **OS:** Ubuntu 20.04 LTS or similar
- **CPU:** 2+ cores
- **RAM:** 2GB minimum, 4GB recommended
- **Storage:** 10GB minimum
- **Network:** Public IP address

### Installation Steps

#### 1. Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3.11 python3.11-venv python3-pip nginx postgresql postgresql-contrib

# Install Node.js (for building frontend)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yasn77/readreceipt.git
sudo chown -R $USER:$USER readreceipt
cd readreceipt
```

#### 3. Setup Python Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

#### 4. Build Frontend

```bash
cd admin-dashboard
npm install
npm run build
cd ..
```

#### 5. Configure Environment

Create `/opt/readreceipt/.env`:

```bash
ADMIN_TOKEN=your-secure-token
SQLALCHEMY_DATABASE_URI=postgresql://readreceipt:db-password@localhost/readreceipt
LOG_LEVEL=WARNING
PORT=5000
```

#### 6. Setup Database

```bash
# Create database user and database
sudo -u postgres psql << EOF
CREATE USER readreceipt WITH PASSWORD 'db-password';
CREATE DATABASE readreceipt OWNER readreceipt;
GRANT ALL PRIVILEGES ON DATABASE readreceipt TO readreceipt;
EOF

# Run migrations
source venv/bin/activate
flask db upgrade
```

#### 7. Create Systemd Service

Create `/etc/systemd/system/readreceipt.service`:

```ini
[Unit]
Description=Read Receipt Application
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/readreceipt
Environment="PATH=/opt/readreceipt/venv/bin"
ExecStart=/opt/readreceipt/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 app:app
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable readreceipt
sudo systemctl start readreceipt

# Check status
sudo systemctl status readreceipt
```

#### 8. Configure nginx

Create `/etc/nginx/sites-available/readreceipt`:

```nginx
server {
    listen 80;
    server_name readreceipt.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name readreceipt.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/readreceipt.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/readreceipt.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/readreceipt/admin-dashboard/dist/;
        try_files $uri $uri/ =404;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/readreceipt /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

#### 9. Setup SSL with Let's Encrypt

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d readreceipt.yourdomain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `ADMIN_TOKEN` | Admin authentication token | `your-secure-token` |
| `SQLALCHEMY_DATABASE_URI` | Database connection string | `postgresql://user:pass@host:5432/db` |

### Optional Variables

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `LOG_LEVEL` | Logging level | `INFO` | `DEBUG`, `WARNING`, `ERROR` |
| `PORT` | Server port | `5000` | `8080` |
| `EXTENSION_ALLOWED_ORIGINS` | Allowed extension domains | `https://mail.google.com` | `https://mail.google.com,https://outlook.live.com` |

### Generating Secure Tokens

```bash
# Using openssl
openssl rand -hex 32

# Using Python
python -c "import secrets; print(secrets.token_hex(32))"

# Using Node.js
node -e "console.log(require('crypto').randomBytes(32).toString('hex'))"
```

## Database Setup

### PostgreSQL Installation

```bash
# Ubuntu/Debian
sudo apt install postgresql postgresql-contrib

# Start PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Create Database and User

```bash
sudo -u postgres psql << EOF
CREATE USER readreceipt WITH PASSWORD 'secure-password';
CREATE DATABASE readreceipt OWNER readreceipt ENCODING 'UTF8';
GRANT ALL PRIVILEGES ON DATABASE readreceipt TO readreceipt;
\c readreceipt
GRANT ALL ON SCHEMA public TO readreceipt;
EOF
```

### Database Optimisation

```sql
-- Create indexes for performance
CREATE INDEX idx_recipients_r_uuid ON recipients(r_uuid);
CREATE INDEX idx_tracking_recipients_id ON tracking(recipients_id);
CREATE INDEX idx_tracking_timestamp ON tracking(timestamp);
CREATE INDEX idx_tracking_ip_country ON tracking(ip_country);

-- Vacuum and analyze
VACUUM ANALYZE;
```

### Connection Pooling

For high-traffic deployments, use PgBouncer:

```bash
# Install PgBouncer
sudo apt install pgbouncer

# Configure /etc/pgbouncer/pgbouncer.ini
[databases]
readreceipt = host=localhost port=5432 dbname=readreceipt

[pgbouncer]
listen_port = 6432
auth_type = md5
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 20
```

## SSL/TLS Configuration

### Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d readreceipt.yourdomain.com

# Certbot auto-configures nginx and sets up auto-renewal
```

### Commercial Certificate

1. Purchase certificate from CA (DigiCert, Sectigo, etc.)
2. Generate CSR:
   ```bash
   openssl req -new -newkey rsa:2048 -nodes -keyout server.key -out server.csr
   ```
3. Submit CSR to CA
4. Install received certificates in nginx

### SSL Best Practices

- Use TLS 1.2 or higher
- Disable weak ciphers
- Enable HSTS
- Renew certificates before expiry
- Use strong key sizes (2048+ bits)

## Production Checklist

### Security

- [ ] Change default `ADMIN_TOKEN`
- [ ] Use HTTPS everywhere
- [ ] Enable firewall (ufw, iptables)
- [ ] Disable root SSH login
- [ ] Use SSH keys instead of passwords
- [ ] Regular security updates
- [ ] Database credentials secured
- [ ] CORS properly configured

### Performance

- [ ] Database indexes created
- [ ] Connection pooling configured
- [ ] Static assets served via CDN (optional)
- [ ] Gzip compression enabled
- [ ] Proper resource limits set

### Reliability

- [ ] Database backups configured
- [ ] Monitoring and alerting setup
- [ ] Log rotation configured
- [ ] Health checks in place
- [ ] Auto-restart on failure
- [ ] Disaster recovery plan

### Compliance

- [ ] Privacy policy in place
- [ ] GDPR compliance (if applicable)
- [ ] Data retention policy defined
- [ ] User consent mechanisms (if required)

## Monitoring Setup

### Prometheus Metrics

Add Prometheus client to Flask app:

```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

### Grafana Dashboard

Import dashboard for visualisation:
- Request rate
- Error rate
- Response time
- Database connections

### Log Aggregation

Use ELK stack or similar:
- Elasticsearch
- Logstash
- Kibana

### Health Checks

```yaml
livenessProbe:
  httpGet:
    path: /
    port: 5000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /
    port: 5000
  initialDelaySeconds: 5
  periodSeconds: 5
```

### Alerting Rules

Example Prometheus alert rules:

```yaml
groups:
- name: readreceipt
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    annotations:
      summary: "High error rate detected"

  - alert: ServiceDown
    expr: up{job="readreceipt"} == 0
    for: 1m
    annotations:
      summary: "Read Receipt service is down"
```

## Backup and Recovery

### Database Backup

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U readreceipt readreceipt > /backups/readreceipt_$DATE.sql
find /backups -name "readreceipt_*.sql" -mtime +7 -delete
```

### Backup Automation

```bash
# Add to crontab
0 2 * * * /opt/readreceipt/scripts/backup.sh
```

### Disaster Recovery

1. **Restore Database:**
   ```bash
   psql -U readreceipt readreceipt < /backups/readreceipt_YYYYMMDD.sql
   ```

2. **Restore Application:**
   ```bash
   git clone https://github.com/yasn77/readreceipt.git
   # Follow installation steps
   ```

3. **Verify:**
   - Test login
   - Check analytics
   - Verify tracking works

## Next Steps

- [Monitoring Guide](troubleshooting.md#monitoring) - Setting up monitoring
- [Troubleshooting](troubleshooting.md) - Common issues
- [Development](development.md) - Development environment

---

**Need help?** See [Troubleshooting](troubleshooting.md) or open an issue on GitHub.
