# Backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (create this file with your dependencies)
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy backend code
COPY . .

COPY .env .

# Create upload directory
RUN mkdir -p uploads

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]