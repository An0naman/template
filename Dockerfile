# template_app/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system packages including fonts for label generation, Bluetooth support, and Git
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    bluez \
    bluetooth \
    libbluetooth-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Ensure the data directory exists for the volume mount (if needed)
# This is where your template.db will reside on the host, mapped into the container
RUN mkdir -p /app/data

# Create uploads directory for static files (will be mounted as volume)
RUN mkdir -p /app/app/static/uploads

# Create repos directory for Git repositories
RUN mkdir -p /app/repos

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy VERSION file for version display
COPY VERSION .

# Copy the entire 'app' package (which contains __init__.py, config.py, db.py, routes/, api/, templates/, static/)
# This ensures all your refactored code is in the correct place inside the container.
COPY app/ app/

# Copy the top-level run.py
COPY run.py .

# Copy scripts directory
COPY scripts/ scripts/

# Copy migrations directory
COPY migrations/ migrations/

# Copy and set up the entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Expose the port your Flask app runs on (from app/config.py's PORT)
# We'll standardize this to 5001 for the container's internal port.
EXPOSE 5001

# Use entrypoint script to run migrations before starting app
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]

# Command to run your Flask application
CMD ["python", "run.py"]

# Healthcheck for container orchestration (Watchtower, Docker Swarm, Kubernetes)
# This ensures the container is actually ready to serve requests
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; import os; import sys; port = os.environ.get('PORT', '5001'); sys.exit(0 if urllib.request.urlopen(f'http://localhost:{port}/api/health').getcode() == 200 else 1)"
