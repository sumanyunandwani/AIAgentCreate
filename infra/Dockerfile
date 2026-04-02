# Use official Python base image (slim variant)
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app/"

# Install system dependencies & update to reduce vulnerabilities
RUN apt-get update && apt-get upgrade -y \
    && apt-get install --no-install-recommends -y python3-pip \
    && pip install --upgrade pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Create Code Directory
RUN mkdir -p /app

# Set the working directory
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code into the container
COPY . .

# Expose FastAPI default port
EXPOSE 8800

# Command to run the app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8800", "--reload", "--workers", "1"]
