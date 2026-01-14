# Python Rclone Web GUI Dockerfile

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install rclone
RUN wget -q https://downloads.rclone.org/rclone-current-linux-amd64.deb \
    && dpkg -i rclone-current-linux-amd64.deb \
    && rm rclone-current-linux-amd64.deb

# Create app directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and startup script
COPY main.py .
COPY startup.sh .
RUN chmod +x startup.sh

# Create data directory for rclone config
RUN mkdir -p /data

# Environment variables
ENV RCLONE_RC_URL=http://localhost:5572
ENV RCLONE_RC_USER=admin
ENV RCLONE_RC_PASS=secret
ENV RCLONE_CONFIG=/data/rclone.conf

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application with startup script
CMD ["./startup.sh"]
