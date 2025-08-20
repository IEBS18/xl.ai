# ==================== SOLUTION 1: Use Official Playwright Image (RECOMMENDED) ====================
# This is the most reliable approach - replace your ./backend/Dockerfile with this:

FROM mcr.microsoft.com/playwright/python:v1.54.0-jammy

WORKDIR /app

# Install additional build dependencies if needed
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .
COPY .env .

# Create necessary directories
RUN mkdir -p uploads outputs

# Environment variables (already set in base image but good to be explicit)
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]

# ==================== SOLUTION 2: Use Ubuntu Base (Alternative) ====================
# If you prefer to stick with a custom setup, use Ubuntu instead of Debian:

# FROM ubuntu:22.04
# 
# # Set environment variables to prevent interactive prompts
# ENV DEBIAN_FRONTEND=noninteractive
# ENV TZ=UTC
# 
# WORKDIR /app
# 
# # Install Python and system dependencies
# RUN apt-get update && apt-get install -y \
#     python3.11 \
#     python3.11-dev \
#     python3-pip \
#     gcc \
#     g++ \
#     wget \
#     gnupg \
#     ca-certificates \
#     && rm -rf /var/lib/apt/lists/*
# 
# # Create symlinks for python
# RUN ln -s /usr/bin/python3.11 /usr/bin/python
# RUN ln -s /usr/bin/pip3 /usr/bin/pip
# 
# # Copy requirements and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# 
# # Install Playwright
# RUN pip install playwright
# RUN playwright install chromium
# RUN playwright install-deps
# 
# # Copy application code
# COPY . .
# COPY .env .
# 
# # Create necessary directories
# RUN mkdir -p uploads outputs
# 
# # Environment variables
# ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# 
# # Expose port
# EXPOSE 5000
# 
# # Run the application
# CMD ["python", "app.py"]

# ==================== SOLUTION 3: Manual Dependencies (Last Resort) ====================
# If you must use python:3.11-slim, manually install dependencies:

# FROM python:3.11-slim
# 
# WORKDIR /app
# 
# # Install system dependencies manually for Playwright
# RUN apt-get update && apt-get install -y \
#     gcc \
#     g++ \
#     wget \
#     gnupg \
#     ca-certificates \
#     fonts-liberation \
#     fonts-unifont \
#     libasound2 \
#     libatk-bridge2.0-0 \
#     libatk1.0-0 \
#     libatspi2.0-0 \
#     libcups2 \
#     libdbus-1-3 \
#     libdrm2 \
#     libgtk-3-0 \
#     libnspr4 \
#     libnss3 \
#     libx11-xcb1 \
#     libxcomposite1 \
#     libxdamage1 \
#     libxfixes3 \
#     libxrandr2 \
#     libxss1 \
#     libxtst6 \
#     xvfb \
#     libgbm1 \
#     libgdk-pixbuf-2.0-0 \
#     libjpeg62-turbo \
#     libpng16-16 \
#     libxcb1 \
#     libxcb-shm0 \
#     libxcb-xfixes0 \
#     && rm -rf /var/lib/apt/lists/*
# 
# # Copy requirements and install Python dependencies
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# 
# # Install Playwright
# RUN pip install playwright
# RUN playwright install chromium --with-deps || playwright install chromium
# 
# # Copy application code
# COPY . .
# COPY .env .
# 
# # Create necessary directories
# RUN mkdir -p uploads outputs
# 
# # Environment variables
# ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
# 
# # Expose port
# EXPOSE 5000
# 
# # Run the application
# CMD ["python", "app.py"]