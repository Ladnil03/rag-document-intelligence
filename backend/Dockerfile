# Production Dockerfile for RAG Document Intelligence Backend
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies needed for compilation and PostgreSQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt-get/lists/*

# Copy dependency requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code into container
COPY . .

# Ensure persistent directories exist with appropriate permissions
RUN mkdir -p storage chroma_data evaluation/reports

# Expose FastAPI server port
EXPOSE 8000

# Health check probe for Docker container status
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/liveness || exit 1

# Production startup command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
