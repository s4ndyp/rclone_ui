#!/bin/bash

echo "🏗️  Building Rclone Web GUI Docker image..."

# Controleer of Docker draait
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Controleer of package-lock.json bestaat
if [ ! -f "frontend/package-lock.json" ]; then
    echo "⚠️  package-lock.json not found in frontend directory. Creating one..."
    cd frontend
    npm install --package-lock-only
    cd ..
fi

# Build de image
echo "🔨 Building Docker image..."
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
    echo ""
    echo "🔍 Check the Docker build output above for error details."
    echo "   Common issues:"
    echo "   - Missing dependencies in package-lock.json"
    echo "   - Rust compilation errors"
    echo "   - Network issues during package downloads"
    exit 1
fi
