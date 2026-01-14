#!/bin/bash

echo "🚀 Deploying Rclone Web GUI from GitHub Container Registry"
echo "Image: ghcr.io/s4ndyp/rclone_ui/rclone_ui:latest"
echo "=" * 60

# Controleer of Docker draait
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Controleer of docker-compose.yml bestaat
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ docker-compose.yml not found in current directory."
    echo "Please run this script from the rclone-web-gui-python directory."
    exit 1
fi

# Maak .env bestand als het niet bestaat
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file from template..."
    cp env.example .env
    echo "✅ .env file created. Edit it to customize your settings."
fi

echo "📥 Pulling latest image from GitHub Container Registry..."
docker pull s4ndyp/rclone_ui/rclone_ui:latest

if [ $? -ne 0 ]; then
    echo "❌ Failed to pull image. Check your internet connection."
    exit 1
fi

echo "🐳 Starting services..."
docker-compose up -d

if [ $? -ne 0 ]; then
    echo "❌ Failed to start services."
    exit 1
fi

echo ""
echo "🎉 Deployment successful!"
echo ""
echo "📱 Access your Rclone Web GUI at: http://localhost:8080"
echo ""
echo "🔧 Other useful commands:"
echo "   docker-compose logs -f              # View logs"
echo "   docker-compose down                # Stop services"
echo "   docker-compose restart             # Restart services"
echo "   docker-compose exec rclone-web-gui bash  # Access container shell"
echo "   docker pull ghcr.io/s4ndyp/rclone_ui/rclone_ui:latest  # Update image"
echo ""
echo "⚙️  To customize settings, edit the .env file and restart:"
echo "   docker-compose down && docker-compose up -d"
