#!/bin/bash

echo "🐍 Building Rclone Web GUI (Python)..."

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

# Build de image
echo "🔨 Building Docker images..."
docker-compose build

if [ $? -eq 0 ]; then
    echo "✅ Build completed successfully!"
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
else
    echo "❌ Build failed!"
    echo ""
    echo "🔍 Check the Docker build output above for error details."
    echo "   Common issues:"
    echo "   - Network issues during pip install"
    echo "   - Missing Python dependencies"
    echo "   - Docker daemon issues"
    exit 1
fi
