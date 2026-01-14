#!/bin/bash

echo "🐍 Setting up Rclone Web GUI (Python)..."

# Controleer of Docker draait
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Controleer of .env bestand bestaat
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from example..."
    cp env.example .env
    echo "✅ Created .env file. You can edit it to customize settings."
fi

# Pull de image
echo "📥 Pulling Docker image: ghcr.io/s4ndyp/rclone_ui/rclone_ui:latest"
docker pull ghcr.io/s4ndyp/rclone_ui:latest

if [ $? -eq 0 ]; then
    echo "✅ Image pull completed successfully!"
    echo ""
    echo "🚀 To start the application:"
    echo "   docker-compose up -d"
    echo ""
    echo "📱 Frontend will be available at: http://localhost:8080"
    echo "🔧 Backend API: http://localhost:8080/api/*"
    echo "🔗 Rclone RC: http://localhost:5572"
    echo ""
    echo "📊 View logs: docker-compose logs -f"
    echo "🛑 Stop: docker-compose down"
    echo ""
    echo "⚙️  Edit .env file to customize settings"
    echo ""
    echo "🔄 If you want to update to the latest version:"
    echo "   docker pull ghcr.io/s4ndyp/rclone_ui/rclone_ui:latest"
else
    echo "❌ Failed to pull image!"
    echo ""
    echo "🔍 Check your internet connection and try again."
    echo "   Or verify the image name: ghcr.io/s4ndyp/rclone_ui/rclone_ui:latest"
    exit 1
fi
