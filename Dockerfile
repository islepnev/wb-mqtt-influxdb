# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install required dependencies
RUN pip install --no-cache-dir -r /app/requirements.txt

# Set entrypoint command
CMD ["python3", "-u", "/app/__main__.py"]
