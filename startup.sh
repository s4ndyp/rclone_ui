#!/bin/bash

set -e

echo "🚀 Starting Rclone Web GUI..."

# Create config directory if it doesn't exist
mkdir -p /data

# Set default config if none exists
if [ ! -f "/data/rclone.conf" ]; then
    echo "📝 Creating default rclone config..."
    touch /data/rclone.conf
fi

# Start rclone RC server in background
echo "🔄 Starting rclone RC server..."
rclone rcd \
    --rc-addr=0.0.0.0:5572 \
    --rc-user=${RCLONE_RC_USER:-admin} \
    --rc-pass=${RCLONE_RC_PASS:-secret} \
    --rc-allow-origin="*" \
    --config=/data/rclone.conf &
RCLONE_PID=$!

# Wait a bit for rclone to start
sleep 3

# Check if rclone is running
if ! kill -0 $RCLONE_PID 2>/dev/null; then
    echo "❌ Failed to start rclone RC server"
    exit 1
fi

echo "✅ Rclone RC server started on port 5572"

# Start the Python web application
echo "🌐 Starting Python web application..."
exec python main.py \
    --host=0.0.0.0 \
    --port=8000 \
    --rclone-url=http://localhost:5572 \
    --rclone-user=${RCLONE_RC_USER:-admin} \
    --rclone-pass=${RCLONE_RC_PASS:-secret}
