FROM python:3.11-slim

WORKDIR /app

# Copy everything from the current directory (New UI) into the container
COPY . .

# Environment variables with defaults
ENV MANAGER_PORT=8080
ENV RCLONE_RC_URL=http://rclone:5572
ENV JOBS_FILE=/data/jobs.json
ENV UI_DIR="." 

# Create data directory for persistent jobs storage
RUN mkdir /data

EXPOSE 8080

# The manager script uses only standard library, so no pip install needed
CMD ["python", "rclone_manager.py"]

