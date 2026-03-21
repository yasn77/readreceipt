# Multi-stage Dockerfile for ReadReceipt
# Builds both backend (Flask) and frontend (React) into a single image

# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy package files
COPY admin-dashboard/package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy frontend source
COPY admin-dashboard/ ./

# Build the frontend
RUN npm run build

# Stage 2: Python Dependencies
FROM python:3.11-slim AS python-deps

WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 3: Final Production Image
FROM python:3.11-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    FLASK_ENV=production \
    ADMIN_TOKEN=change-me-in-production \
    LOG_LEVEL=INFO \
    SQLALCHEMY_DATABASE_URI=sqlite:////app/data/readreceipt.db \
    EXTENSION_ALLOWED_ORIGINS=https://mail.google.com,https://outlook.live.com \
    PATH=/root/.local/bin:$PATH

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for SQLite
RUN mkdir -p /app/data

# Copy Python dependencies from python-deps stage
COPY --from=python-deps /root/.local /root/.local

# Copy backend source code
COPY src/ ./src/
COPY migrations/ ./migrations/

# Copy frontend build from frontend-builder stage
COPY --from=frontend-builder /app/frontend/dist/ ./src/readreceipt/static/

# Create non-root user for security
RUN useradd -m -u 1000 readreceipt && \
    chown -R readreceipt:readreceipt /app

# Switch to non-root user
USER readreceipt

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Entrypoint script
COPY --chown=readreceipt:readreceipt docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["gunicorn", "--bind=0.0.0.0:8000", "--workers=4", "--threads=2", "--timeout=60", "--access-logfile=-", "--error-logfile=-", "src.readreceipt.app:app"]
