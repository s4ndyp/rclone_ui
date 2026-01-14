#!/bin/bash

set -e

echo "🚀 Starting Rclone Web GUI..."

# Functie om te controleren of een proces draait
check_process() {
    local pid=$1
    if kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Functie om schoon af te sluiten
cleanup() {
    echo "🛑 Shutting down..."
    if [ ! -z "$RCLONE_PID" ]; then
        kill $RCLONE_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    exit 0
}

# Trap voor schoon afsluiten
trap cleanup SIGTERM SIGINT

# Controleer of rclone config bestaat, maak lege config als niet
if [ ! -f "$RCLONE_CONFIG" ]; then
    echo "📝 Creating empty rclone config..."
    touch "$RCLONE_CONFIG"
fi

# Start rclone RC server in de achtergrond
echo "🔄 Starting rclone RC server..."
rclone rcd \
    --rc-addr="$RCLONE_RC_ADDR" \
    --rc-user="$RCLONE_RC_USER" \
    --rc-pass="$RCLONE_RC_PASS" \
    --rc-allow-origin="*" \
    --config="$RCLONE_CONFIG" &
RCLONE_PID=$!

echo "⏳ Waiting for rclone RC server to start..."
sleep 3

# Controleer of rclone draait
if ! check_process $RCLONE_PID; then
    echo "❌ Failed to start rclone RC server"
    exit 1
fi

echo "✅ Rclone RC server started on $RCLONE_RC_ADDR"

# Start de Rust backend
echo "🔧 Starting backend server..."
./backend \
    --bind="0.0.0.0:$BACKEND_PORT" \
    --rclone-url="http://localhost:5572" \
    --username="$RCLONE_RC_USER" \
    --password="$RCLONE_RC_PASS" &
BACKEND_PID=$!

echo "⏳ Waiting for backend to start..."
sleep 2

# Controleer of backend draait
if ! check_process $BACKEND_PID; then
    echo "❌ Failed to start backend server"
    cleanup
fi

echo "✅ Backend server started on port $BACKEND_PORT"

# Controleer of we een webserver nodig hebben voor de frontend
if command -v python3 &> /dev/null; then
    WEBSERVER_CMD="python3 -m http.server $FRONTEND_PORT"
elif command -v node &> /dev/null && [ -f "frontend/package.json" ]; then
    # Als we npm hebben, gebruik dan een eenvoudige static server
    cd frontend && npm install -g serve && cd ..
    WEBSERVER_CMD="serve -s frontend -l $FRONTEND_PORT"
else
    echo "⚠️  No suitable webserver found, trying to use busybox httpd"
    WEBSERVER_CMD="busybox httpd -f -p $FRONTEND_PORT -h frontend"
fi

# Start frontend webserver
echo "🌐 Starting frontend server on port $FRONTEND_PORT..."
$WEBSERVER_CMD &
FRONTEND_PID=$!

echo "⏳ Waiting for frontend to start..."
sleep 1

# Controleer of frontend draait
if ! check_process $FRONTEND_PID; then
    echo "❌ Failed to start frontend server"
    cleanup
fi

echo "✅ Frontend server started on port $FRONTEND_PORT"
echo ""
echo "🎉 Rclone Web GUI is running!"
echo "📱 Frontend: http://localhost:$FRONTEND_PORT"
echo "🔧 Backend: http://localhost:$BACKEND_PORT"
echo "🔗 Rclone RC: http://localhost:5572"
echo ""
echo "Press Ctrl+C to stop all services"

# Wacht tot een proces stopt
wait $RCLONE_PID $BACKEND_PID $FRONTEND_PID

echo "⚠️  One of the services stopped unexpectedly"
cleanup
