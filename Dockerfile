# Production Dockerfile for Compliance Autopilot
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for persistent storage
RUN mkdir -p /app/data

# Environment variables
ENV DATABASE_URL=sqlite:///data/compliance_autopilot.db
ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Initialize database on startup and run server
CMD sh -c "python3 -c 'from app.models.database import init_db; init_db()' && \
    python3 -c 'from app.scripts.seed_historic_circulars import seed_historic_circulars; seed_historic_circulars()' && \
    uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2"