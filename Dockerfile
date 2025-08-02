# template_app/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system packages including fonts for label generation
RUN apt-get update && apt-get install -y \
    fonts-dejavu-core \
    fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

# Ensure the data directory exists for the volume mount (if needed)
# This is where your template.db will reside on the host, mapped into the container
RUN mkdir -p /app/data

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire 'app' package (which contains __init__.py, config.py, db.py, routes/, api/, templates/, static/)
# This ensures all your refactored code is in the correct place inside the container.
COPY app/ app/

# Copy the top-level run.py
COPY run.py .

# Copy the cron script for overdue checking
COPY cron_check_overdue.sh .

# Expose the port your Flask app runs on (from app/config.py's PORT)
# We'll standardize this to 5000 for the container's internal port.
EXPOSE 5000

# Command to run your Flask application
CMD ["python", "run.py"]
