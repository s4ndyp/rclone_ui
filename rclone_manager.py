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

# MongoDB configuration for direct access
MONGODB_URL = os.environ.get('MONGODB_URL', 'http://10.10.2.20:5000')
CLIENT_ID = os.environ.get('CLIENT_ID', 'sandman')
APP_NAME = os.environ.get('APP_NAME', 'rclone')

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

# --- MONGODB CLIENT ---
class MongoClient:
    def __init__(self, base_url, client_id, app_name):
        self.base_url = base_url
        self.client_id = client_id
        self.app_name = app_name

    def _get_url(self, collection_name, id=None):
        url = f"{self.base_url}/api/{self.app_name}_{collection_name}"
        if id:
            url += f"/{id}"
        return url

    def get_collection(self, name):
        """Get all documents from a collection"""
        try:
            import urllib.request
            import urllib.parse
            import json

            url = self._get_url(name)
            req = urllib.request.Request(url, headers={'x-client-id': self.client_id})

            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[{datetime.now()}] MongoDB get_collection error for {name}: {e}", flush=True)
            return []

    def get_document(self, name, id):
        """Get a single document by ID"""
        try:
            import urllib.request
            import json

            url = self._get_url(name, id)
            req = urllib.request.Request(url, headers={'x-client-id': self.client_id})

            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"[{datetime.now()}] MongoDB get_document error for {name}/{id}: {e}", flush=True)
            return None

# Global MongoDB client
mongo_client = MongoClient(MONGODB_URL, CLIENT_ID, APP_NAME)

# --- TASKS ---

def run_backup(job):
    print(f"[{datetime.now()}] Starting Backup: {job['name']}", flush=True)

    # Reset stats so that core/stats only reflects the current backup
    # This fulfills the requirement of "activating" stats only for the new start
    print(f"[{datetime.now()}] Resetting rclone stats...", flush=True)
    rclone_rc_call("core/stats-reset")

    # Using sync/copy as it's safer than sync/sync for backups
    params = {
        "srcFs": job['source'],
        "dstFs": job['dest'],
        "_async": True
    }
    res = rclone_rc_call("sync/copy", params)
    if res and 'jobid' in res:
        print(f"[{datetime.now()}] Backup {job['name']} started. Job ID: {res['jobid']}", flush=True)
        return res['jobid']
    else:
        print(f"[{datetime.now()}] Failed to start backup {job['name']}", flush=True)
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
    import sys
    print(f"[{datetime.now()}] Scheduler started - using MongoDB direct access.", flush=True)
    last_run = {} # Keep track of last run time per job to avoid double starts

    while True:
        # Load jobs directly from MongoDB instead of jobs.json
        mongo_jobs = mongo_client.get_collection('jobs')
        jobs = []

        # Convert MongoDB jobs to scheduler format
        for job in mongo_jobs:
            job_id = job.get('id') or job.get('_id')
            schedule_data = None

            # Load schedule from separate collection if referenced
            job_schedule = job.get('schedule')
            if job_schedule and isinstance(job_schedule, dict) and job_schedule.get('_id'):
                schedule_doc = mongo_client.get_document('job_schedules', job_schedule['_id'])
                if schedule_doc:
                    schedule_data = {
                        'time': schedule_doc.get('time'),
                        'days': schedule_doc.get('days', [])
                    }
            elif job_schedule and isinstance(job_schedule, dict):
                # Legacy inline schedule
                schedule_data = job_schedule

            scheduler_job = {
                'id': job_id,
                'name': job.get('name'),
                'type': job.get('type'),
                'source': job.get('source'),
                'dest': job.get('dest'),
                'schedule': schedule_data,
                'enabled': job.get('enabled', True),
                'excludes': job.get('excludes', [])
            }
            jobs.append(scheduler_job)

        now = datetime.now()
        current_time = now.strftime("%H:%M")
        current_day = now.weekday() + 1  # Monday = 1, Sunday = 7 (to match our frontend)

        # Log every minute for better monitoring
        should_log = now.second < 30

        if should_log:
            print(f"[{datetime.now()}] Scheduler check - Time: {current_time}, Day: {current_day}, Jobs: {len(jobs)} (from MongoDB)", flush=True)

        for job in jobs:
            job_name = job.get('name', job.get('id', 'unknown'))

            if job.get('type') == 'backup' and job.get('schedule') and job.get('enabled', True):
                schedule = job['schedule']

                # Check if job should run at current time
                should_run = False

                if isinstance(schedule, str):
                    # Old format: just time string (backwards compatibility)
                    should_run = schedule == current_time
                    if should_run:
                        print(f"[{datetime.now()}] OLD FORMAT: Job '{job_name}' scheduled for {schedule}", flush=True)
                elif isinstance(schedule, dict) and 'time' in schedule:
                    # New format: {time: "HH:MM", days: [1,2,3,4,5]}
                    schedule_time = schedule['time']
                    schedule_days = schedule.get('days', [1, 2, 3, 4, 5])  # Default Monday-Friday

                    time_match = schedule_time == current_time
                    day_match = current_day in schedule_days
                    should_run = time_match and day_match

                    if should_run:
                        print(f"[{datetime.now()}] SCHEDULED RUN: Job '{job_name}' should run at {current_time} on day {current_day} (days: {schedule_days})", flush=True)

                if should_run:
                    job_id = job.get('id')
                    run_key = f"{job_id}_{current_time}_{current_day}"
                    if last_run.get(job_id) != run_key:
                        print(f"[{datetime.now()}] EXECUTING scheduled run for job {job_name}", flush=True)
                        run_backup(job)
                        last_run[job_id] = run_key
                    else:
                        print(f"[{datetime.now()}] Skipping duplicate run for job {job_name}", flush=True)

        time.sleep(60)  # Check every minute instead of 30 seconds

# --- API & SERVER ---

class RcloneManagerHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=UI_DIR, **kwargs)

    def do_POST(self):
        if self.path == '/api/sync_jobs':
            # Sync jobs from MongoDB to jobs.json
            try:
                # This endpoint expects jobs data in the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                mongo_jobs = json.loads(post_data)

                # Convert MongoDB jobs to scheduler format
                scheduler_jobs = []
                for job in mongo_jobs:
                    scheduler_job = {
                        'id': job.get('id') or job.get('_id'),
                        'name': job.get('name'),
                        'type': job.get('type'),
                        'source': job.get('source'),
                        'dest': job.get('dest'),
                        'schedule': job.get('schedule'),
                        'enabled': job.get('enabled', True),
                        'excludes': job.get('excludes', [])
                    }
                    scheduler_jobs.append(scheduler_job)

                save_jobs(scheduler_jobs)
                print(f"[{datetime.now()}] Synced {len(scheduler_jobs)} jobs from MongoDB to jobs.json", flush=True)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'synced', 'count': len(scheduler_jobs)}).encode())

            except Exception as e:
                print(f"[{datetime.now()}] Error syncing jobs: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
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

            # Load job directly from MongoDB
            job_doc = mongo_client.get_document('jobs', data['id'])
            if job_doc:
                job_id = job_doc.get('id') or job_doc.get('_id')
                schedule_data = None

                # Load schedule from separate collection if referenced
                job_schedule = job_doc.get('schedule')
                if job_schedule and isinstance(job_schedule, dict) and job_schedule.get('_id'):
                    schedule_doc = mongo_client.get_document('job_schedules', job_schedule['_id'])
                    if schedule_doc:
                        schedule_data = {
                            'time': schedule_doc.get('time'),
                            'days': schedule_doc.get('days', [])
                        }
                elif job_schedule and isinstance(job_schedule, dict):
                    # Legacy inline schedule
                    schedule_data = job_schedule

                job = {
                    'id': job_id,
                    'name': job_doc.get('name'),
                    'type': job_doc.get('type'),
                    'source': job_doc.get('source'),
                    'dest': job_doc.get('dest'),
                    'schedule': schedule_data,
                    'enabled': job_doc.get('enabled', True),
                    'excludes': job_doc.get('excludes', [])
                }
            else:
                job = None
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
        elif self.path == '/api/sync_jobs':
            # Sync jobs from MongoDB to jobs.json
            try:
                # This endpoint expects jobs data in the request body
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                mongo_jobs = json.loads(post_data)

                # Convert MongoDB jobs to scheduler format
                scheduler_jobs = []
                for job in mongo_jobs:
                    scheduler_job = {
                        'id': job.get('id') or job.get('_id'),
                        'name': job.get('name'),
                        'type': job.get('type'),
                        'source': job.get('source'),
                        'dest': job.get('dest'),
                        'schedule': job.get('schedule'),
                        'enabled': job.get('enabled', True),
                        'excludes': job.get('excludes', [])
                    }
                    scheduler_jobs.append(scheduler_job)

                save_jobs(scheduler_jobs)
                print(f"[{datetime.now()}] Synced {len(scheduler_jobs)} jobs from MongoDB to jobs.json", flush=True)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'synced', 'count': len(scheduler_jobs)}).encode())

            except Exception as e:
                print(f"[{datetime.now()}] Error syncing jobs: {e}", flush=True)
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())

        elif self.path == '/api/scheduler_status':
            # Debug endpoint to check scheduler status
            now = datetime.now()
            jobs_data = load_jobs()

            print(f"[{datetime.now()}] Scheduler status requested. Jobs in file: {len(jobs_data)}", flush=True)
            for job in jobs_data:
                job_name = job.get('name', 'unnamed')
                job_schedule = job.get('schedule')
                print(f"[{datetime.now()}] File job '{job_name}' - schedule: {job_schedule}", flush=True)

            status = {
                'current_time': now.strftime("%H:%M:%S"),
                'current_day': now.weekday() + 1,  # Monday = 1, Sunday = 7
                'timezone': str(now.tzinfo) if now.tzinfo else 'UTC',
                'jobs_count': len(jobs_data),
                # Load schedules for status display
                schedules_data = mongo_client.get_collection('job_schedules')
                schedule_map = {s.get('jobId'): s for s in schedules_data}

                'jobs': [
                    {
                        'name': job.get('name', 'unnamed'),
                        'type': job.get('type'),
                        'schedule': schedule_map.get(job.get('id') or job.get('_id'), {}).get('time') if schedule_map.get(job.get('id') or job.get('_id')) else None,
                        'enabled': job.get('enabled', True)
                    }
                    for job in jobs_data
                ]
            }
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(status, indent=2).encode())
        else:
            return super().do_GET()

def run_server():
    print(f"[{datetime.now()}] Checking rclone connection at {RCLONE_RC_URL}...", flush=True)
    version = rclone_rc_call("core/version")
    if version:
        print(f"[{datetime.now()}] Connected to rclone version: {version.get('version')}", flush=True)
    else:
        print(f"[{datetime.now()}] WARNING: Could not connect to rclone. Make sure it's running with --rc.", flush=True)

    with socketserver.TCPServer(("", PORT), RcloneManagerHandler) as httpd:
        print(f"[{datetime.now()}] Serving UI at http://localhost:{PORT}", flush=True)
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

