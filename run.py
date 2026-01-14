#!/usr/bin/env python3
"""
Development runner for Rclone Web GUI (Python)
"""

import os
import subprocess
import sys
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        print("✅ Python dependencies installed")
    except ImportError:
        print("❌ Python dependencies not found. Run: pip install -r requirements.txt")
        return False

    # Check if rclone is available
    try:
        result = subprocess.run(['rclone', 'version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ rclone found")
        else:
            print("❌ rclone not found or not working")
            return False
    except FileNotFoundError:
        print("❌ rclone not found. Please install rclone first.")
        return False

    return True

def start_rclone_rc():
    """Start rclone RC server in background"""
    print("🔄 Starting rclone RC server...")

    # Check if rclone config exists
    config_path = Path.home() / ".config" / "rclone" / "rclone.conf"
    if not config_path.exists():
        print(f"⚠️  Rclone config not found at {config_path}")
        print("   Please configure rclone first: rclone config")
        return None

    cmd = [
        "rclone", "rcd",
        "--rc-addr=localhost:5572",
        "--rc-user=admin",
        "--rc-pass=secret",
        "--rc-allow-origin=*"
    ]

    try:
        process = subprocess.Popen(cmd)
        print("✅ Rclone RC server started on http://localhost:5572")
        return process
    except Exception as e:
        print(f"❌ Failed to start rclone RC: {e}")
        return None

def main():
    print("🐍 Rclone Web GUI (Python) - Development Mode")
    print("=" * 50)

    if not check_dependencies():
        sys.exit(1)

    # Start rclone RC server
    rclone_process = start_rclone_rc()
    if not rclone_process:
        print("❌ Cannot start without rclone RC server")
        sys.exit(1)

    try:
        # Start the web application
        print("🌐 Starting web application...")
        print("📱 Open your browser to: http://localhost:8000")
        print("🛑 Press Ctrl+C to stop")

        # Run the FastAPI application
        os.system("python main.py --host localhost --port 8000")

    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        if rclone_process:
            rclone_process.terminate()
            rclone_process.wait()
        print("✅ Cleanup complete")

if __name__ == "__main__":
    main()
