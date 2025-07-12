# template_app/Dockerfile
FROM python:3.12-slim

WORKDIR /app

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

# Expose the port your Flask app runs on (from app/config.py's PORT)
# We'll standardize this to 5000 for the container's internal port.
EXPOSE 5000

# Command to run your Flask application
CMD ["python", "run.py"]
