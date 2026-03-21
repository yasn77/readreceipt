# Docker Deployment Guide

This guide covers deploying ReadReceipt using Docker and Docker Compose.

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/yasn77/readreceipt.git
cd readreceipt

# 2. Set up environment variables
cp .env.docker.example .env
# Edit .env and set a secure ADMIN_TOKEN

# 3. Start with Docker Compose
docker-compose up -d

# 4. Access the application
open http://localhost:8000
```

## Architecture

The Docker setup uses a multi-stage build process:

1. **Frontend Builder Stage** (`node:20-alpine`)
   - Builds the React admin dashboard
   - Outputs static files to `dist/`

2. **Python Dependencies Stage** (`python:3.11-slim`)
   - Installs Python packages
   - Compiles native extensions

3. **Production Stage** (`python:3.11-slim`)
   - Minimal runtime image
   - Combines backend and frontend
   - Runs as non-root user

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADMIN_TOKEN` | Yes | `change-me-in-production` | Admin authentication token |
| `SQLALCHEMY_DATABASE_URI` | No | `sqlite:////app/data/readreceipt.db` | Database connection string |
| `EXTENSION_ALLOWED_ORIGINS` | No | `https://mail.google.com` | Allowed extension origins |
| `LOG_LEVEL` | No | `INFO` | Logging verbosity |
| `PORT` | No | `8000` | Server port |
| `SECRET_KEY` | No | Random | Flask secret key |

### Using PostgreSQL

For production, use PostgreSQL instead of SQLite:

```yaml
# docker-compose.yml (uncomment postgres service)
services:
  readreceipt:
    environment:
      - SQLALCHEMY_DATABASE_URI=postgresql://readreceipt:changeme@postgres:5432/readreceipt
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=readreceipt
      - POSTGRES_PASSWORD=changeme
      - POSTGRES_DB=readreceipt
    volumes:
      - postgres-data:/var/lib/postgresql/data
```

## Commands

### Build

```bash
# Build the image
docker-compose build

# Build with no cache
docker-compose build --no-cache

# Build specific stage
docker build --target frontend-builder -t readreceipt-frontend .
```

### Run

```bash
# Start in detached mode
docker-compose up -d

# Start with logs
docker-compose up

# Start specific service
docker-compose up -d readreceipt
```

### Stop

```bash
# Stop containers
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Logs

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f readreceipt

# View last 100 lines
docker-compose logs --tail=100
```

### Updates

```bash
# Pull latest changes
git pull origin master

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations
docker-compose exec readreceipt flask --app src/readreceipt/app.py db upgrade
```

## Data Persistence

### Volumes

- `readreceipt-data`: SQLite database and application data
- `postgres-data`: PostgreSQL data (if using PostgreSQL)

### Backup

```bash
# Backup SQLite database
docker run --rm \
  -v readreceipt-data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/readreceipt-backup-$(date +%Y%m%d).tar.gz -C /data .

# Backup PostgreSQL
docker-compose exec postgres pg_dump -U readreceipt readreceipt > backup.sql
```

### Restore

```bash
# Restore SQLite
docker run --rm \
  -v readreceipt-data:/data \
  -v $(pwd):/backup \
  alpine sh -c "cd /data && tar xzf /backup/readreceipt-backup-YYYYMMDD.tar.gz"

# Restore PostgreSQL
docker-compose exec -T postgres psql -U readreceipt readreceipt < backup.sql
```

## Health Checks

The container includes a health check endpoint:

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

## Development

Use the development override file for hot-reload:

```bash
# The override file is automatically loaded
docker-compose up -d

# View logs
docker-compose logs -f

# Make code changes and see them reflected immediately
```

## Production Deployment

### Security Checklist

- [ ] Change default `ADMIN_TOKEN`
- [ ] Set strong `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Configure proper firewall rules
- [ ] Set up log aggregation
- [ ] Enable automated backups
- [ ] Use secrets management (Docker Swarm/Kubernetes)

### Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Deploy stack
docker stack deploy -c docker-compose.yml readreceipt

# Scale service
docker service scale readreceipt_readreceipt=3
```

### Traefik (Reverse Proxy)

```yaml
# docker-compose.traefik.yml
version: '3.8'

services:
  readreceipt:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.readreceipt.rule=Host(`readreceipt.example.com`)"
      - "traefik.http.routers.readreceipt.tls.certresolver=letsencrypt"
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs readreceipt

# Check environment variables
docker-compose config

# Run with debug output
docker-compose up --verbose
```

### Database Connection Issues

```bash
# Check database connectivity
docker-compose exec readreceipt python -c "
from src.readreceipt.app import db
from sqlalchemy import text
db.session.execute(text('SELECT 1'))
print('Database connection OK')
"
```

### Reset Everything

```bash
# Remove all containers, volumes, and images
docker-compose down -v --rmi all

# Remove data volumes
docker volume rm readreceipt_readreceipt-data

# Start fresh
docker-compose up -d
```

## Monitoring

### Prometheus Metrics

Enable Prometheus metrics by setting:

```env
PROMETHEUS_MULTIPROC_DIR=/tmp/prometheus
```

Access metrics at: `http://localhost:8000/metrics`

### Resource Usage

```bash
# View container stats
docker stats readreceipt

# View resource limits
docker-compose exec readreceipt cat /proc/1/status
```

## Support

For issues and questions:
- GitHub Issues: https://github.com/yasn77/readreceipt/issues
- Documentation: https://github.com/yasn77/readreceipt/tree/master/docs
