import json
import time
import subprocess
import threading
import os
import http.server
import socketserver
from datetime import datetime
import urllib.request
import urllib.parse

# --- CONFIGURATION ---
PORT = int(os.environ.get('MANAGER_PORT', 8080))
RCLONE_RC_URL = os.environ.get('RCLONE_RC_URL', 'http://127.0.0.1:5572')
RCLONE_USER = os.environ.get('RCLONE_USER', '')
RCLONE_PASS = os.environ.get('RCLONE_PASS', '')
JOBS_FILE = os.environ.get('JOBS_FILE', 'jobs.json')

# Default to current directory if index.html is present, otherwise 'New UI'
default_ui_dir = '.' if os.path.exists('index.html') else 'New UI'
UI_DIR = os.environ.get('UI_DIR', default_ui_dir)

# --- HELPERS ---

def rclone_rc_call(method, params=None):
    url = f"{RCLONE_RC_URL}/{method}"
    data = json.dumps(params or {}).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    
    if RCLONE_USER and RCLONE_PASS:
        import base64
        auth = base64.b64encode(f"{RCLONE_USER}:{RCLONE_PASS}".encode('utf-8')).decode('utf-8')
        req.add_header('Authorization', f'Basic {auth}')
    
    try:
        with urllib.request.urlopen(req) as f:
            return json.loads(f.read().decode('utf-8'))
    except Exception as e:
        print(f"[{datetime.now()}] Rclone RC Error ({method}): {e}")
        return None

def load_jobs():
    if os.path.exists(JOBS_FILE):
        try:
            with open(JOBS_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

def save_jobs(jobs):
    with open(JOBS_FILE, 'w') as f:
        json.dump(jobs, f, indent=4)

# --- TASKS ---

def run_backup(job):
    print(f"[{datetime.now()}] Starting Backup: {job['name']}")
    # Using sync/copy as it's safer than sync/sync for backups
    params = {
        "srcFs": job['source'],
        "dstFs": job['dest'],
        "_async": True
    }
    res = rclone_rc_call("sync/copy", params)
    if res and 'jobid' in res:
        print(f"[{datetime.now()}] Backup {job['name']} started. Job ID: {res['jobid']}")
        return res['jobid']
    return None

def mount_remotes():
    jobs = load_jobs()
    for job in jobs:
        if job.get('type') == 'mount' and job.get('enabled', True):
            remote = job.get('source')
            path = job.get('dest')
            print(f"[{datetime.now()}] Mounting {remote} to {path}...")
            res = rclone_rc_call("mount/mount", {"fs": remote, "mountPoint": path})
            if res is not None:
                print(f"[{datetime.now()}] Mount successful for {remote}")
            else:
                print(f"[{datetime.now()}] Mount failed for {remote}")

# --- SCHEDULER ---

def scheduler():
    print(f"[{datetime.now()}] Scheduler started.")
    last_run = {} # Keep track of last run time per job to avoid double starts
    
    while True:
        jobs = load_jobs()
        now = datetime.now()
        current_time = now.strftime("%H:%M")
        
        for job in jobs:
            if job.get('type') == 'backup' and job.get('schedule') and job.get('enabled', True):
                sched = job['schedule'] # Expected format "HH:MM"
                
                if sched == current_time:
                    job_id = job.get('id')
                    if last_run.get(job_id) != current_time:
                        run_backup(job)
                        last_run[job_id] = current_time
        
        time.sleep(30)

# --- API & SERVER ---

class RcloneManagerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/jobs':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            jobs = json.loads(post_data)
            save_jobs(jobs)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        elif self.path == '/api/get_jobs':
            jobs = load_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(jobs).encode())
        elif self.path == '/api/run_job':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            jobs = load_jobs()
            job = next((j for j in jobs if j['id'] == data['id']), None)
            if job:
                jobid = run_backup(job)
                self.send_response(200)
                self.end_headers()
                self.wfile.write(json.dumps({"status": "started", "jobid": jobid}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        else:
            # Proxy to rclone RC
            if self.path.startswith('/rc/'):
                method = self.path[4:]
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data)
                res = rclone_rc_call(method, params)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(res).encode())

    def do_GET(self):
        if self.path == '/api/get_jobs':
            jobs = load_jobs()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(jobs).encode())
        else:
            return super().do_GET()

def run_server():
    print(f"[{datetime.now()}] Checking rclone connection at {RCLONE_RC_URL}...")
    version = rclone_rc_call("core/version")
    if version:
        print(f"[{datetime.now()}] Connected to rclone version: {version.get('version')}")
    else:
        print(f"[{datetime.now()}] WARNING: Could not connect to rclone. Make sure it's running with --rc.")

    with socketserver.TCPServer(("", PORT), RcloneManagerHandler) as httpd:
        print(f"[{datetime.now()}] Serving UI at http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    # Ensure UI directory exists
    if not os.path.exists(UI_DIR):
        print(f"Error: {UI_DIR} directory not found.")
        exit(1)

    # Initial mount
    # mount_remotes() # Uncomment if you want auto-mount on start

    # Start scheduler thread
    sched_thread = threading.Thread(target=scheduler, daemon=True)
    sched_thread.start()

    # Start server
    try:
        run_server()
    except KeyboardInterrupt:
        print("\nShutting down...")

