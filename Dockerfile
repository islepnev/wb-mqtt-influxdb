# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app

# Install required dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Set entrypoint command
CMD ["python", "__main__.py"]
