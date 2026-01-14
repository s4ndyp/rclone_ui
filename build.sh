#!/bin/bash

echo "🏗️  Building Rclone Web GUI Docker image..."

# Controleer of Docker draait
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Build de image
docker build -t rclone-web-gui:latest .

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
    echo ""
    echo "🚀 To run the application:"
    echo "   docker-compose up -d"
    echo ""
    echo "📱 Frontend will be available at: http://localhost:8080"
    echo "🔧 Backend API: http://localhost:3001"
    echo "🔗 Rclone RC: http://localhost:5572"
    echo ""
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose down"
else
    echo "❌ Build failed!"
    exit 1
fi
