# Multi-stage build voor rclone-web-gui

# Stage 1: Build Rust backend
FROM rust:1.83-slim AS rust-builder
WORKDIR /app/backend
COPY backend/Cargo.toml backend/Cargo.lock ./
COPY backend/src ./src
RUN apt-get update && apt-get install -y pkg-config libssl-dev
RUN cargo build --release

# Stage 2: Build React frontend
FROM node:20-alpine AS node-builder
WORKDIR /app/frontend
COPY frontend/ ./
RUN npm install
RUN npm run build

# Stage 3: Runtime image
FROM debian:bookworm-slim

# Installeer systeem dependencies
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    ca-certificates \
    nginx \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Installeer rclone (laatste versie)
RUN wget -q https://downloads.rclone.org/rclone-current-linux-amd64.deb \
    && dpkg -i rclone-current-linux-amd64.deb \
    && rm rclone-current-linux-amd64.deb

# Maak app directory
WORKDIR /app

# Kopieer gecompileerde backend
COPY --from=rust-builder /app/backend/target/release/rclone-web-gui-backend ./backend

# Kopieer gebouwde frontend naar nginx
COPY --from=node-builder /app/frontend/dist /var/www/html

# Kopieer configuratiebestanden
COPY docker/nginx.conf /etc/nginx/sites-available/default
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Kopieer startup script
COPY docker/startup.sh ./
RUN chmod +x startup.sh

# Maak data directory voor rclone config
RUN mkdir -p /data

# Environment variables
ENV RCLONE_CONFIG=/data/rclone.conf
ENV FRONTEND_PORT=80
ENV BACKEND_PORT=3001
ENV RCLONE_RC_ADDR=localhost:5572
ENV RCLONE_RC_USER=admin
ENV RCLONE_RC_PASS=secret

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Expose ports
EXPOSE 80 3001

# Start alles met supervisor
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
