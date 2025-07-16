FROM python:3.9-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libc6-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r ipanel && useradd -r -g ipanel ipanel

WORKDIR /app

# Install Python dependencies
COPY iPanel/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY iPanel/ ./iPanel/

# Set ownership
RUN chown -R ipanel:ipanel /app

# Switch to non-root user
USER ipanel

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8888/health || exit 1

# Expose port
EXPOSE 8888

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

# Start application
CMD ["python", "iPanel/runserver.py"]

# Production stage
FROM base AS production

# Additional security measures
RUN pip install --no-cache-dir gunicorn[gevent]

# Copy gunicorn configuration
COPY docker/gunicorn.conf.py /app/

# Override CMD for production
CMD ["gunicorn", "--config", "gunicorn.conf.py", "iPanel.runserver:app"]
