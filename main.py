#!/usr/bin/env python3

import os
import subprocess
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Rclone Web GUI", description="Web interface for rclone", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
RCLONE_RC_URL = os.getenv("RCLONE_RC_URL", "http://localhost:5572")
RCLONE_RC_USER = os.getenv("RCLONE_RC_USER", "admin")
RCLONE_RC_PASS = os.getenv("RCLONE_RC_PASS", "secret")

class RcloneClient:
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.auth = (username, password) if username and password else None

    def _make_request(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make a request to rclone RC API"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        try:
            if data:
                response = requests.post(url, json=data, auth=self.auth, headers=headers, timeout=30)
            else:
                response = requests.post(url, auth=self.auth, headers=headers, timeout=30)

            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=500, detail=f"Rclone RC error: {str(e)}")

    def health_check(self) -> Dict[str, Any]:
        """Check if rclone RC is responding"""
        return self._make_request("rc/noopauth")

    def list_remotes(self) -> List[str]:
        """List all configured remotes"""
        result = self._make_request("config/listremotes")
        return result.get("remotes", [])

    def list_files(self, fs: str, remote: str = "") -> List[Dict[str, Any]]:
        """List files in a remote"""
        data = {"fs": fs, "remote": remote}
        result = self._make_request("operations/list", data)
        return result.get("list", [])

    def get_config_dump(self) -> Dict[str, Any]:
        """Get all remote configurations"""
        return self._make_request("config/dump")

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List running jobs"""
        result = self._make_request("job/list")
        job_ids = result.get("jobids", [])
        return [{"id": job_id} for job_id in job_ids]

    def list_mounts(self) -> List[Dict[str, Any]]:
        """List active mounts"""
        result = self._make_request("mount/listmounts")
        mount_points = result.get("mountPoints", [])
        return [{"mount_point": point} for point in mount_points]

    def create_mount(self, fs: str, mount_point: str) -> Dict[str, Any]:
        """Create a new mount"""
        data = {"fs": fs, "mountPoint": mount_point}
        return self._make_request("mount/mount", data)

    def unmount(self, mount_point: str) -> Dict[str, Any]:
        """Unmount a mount point"""
        data = {"mountPoint": mount_point}
        return self._make_request("mount/unmount", data)

    def copy_file(self, src_fs: str, src_remote: str, dst_fs: str, dst_remote: str) -> Dict[str, Any]:
        """Copy a file"""
        data = {
            "srcFs": src_fs,
            "srcRemote": src_remote,
            "dstFs": dst_fs,
            "dstRemote": dst_remote,
            "_async": True
        }
        return self._make_request("operations/copyfile", data)

    def move_file(self, src_fs: str, src_remote: str, dst_fs: str, dst_remote: str) -> Dict[str, Any]:
        """Move a file"""
        data = {
            "srcFs": src_fs,
            "srcRemote": src_remote,
            "dstFs": dst_fs,
            "dstRemote": dst_remote,
            "_async": True
        }
        return self._make_request("operations/movefile", data)

    def delete_file(self, fs: str, remote: str) -> Dict[str, Any]:
        """Delete a file"""
        data = {"fs": fs, "remote": remote}
        return self._make_request("operations/deletefile", data)

    def create_directory(self, fs: str, remote: str) -> Dict[str, Any]:
        """Create a directory"""
        data = {"fs": fs, "remote": remote}
        return self._make_request("operations/mkdir", data)

# Initialize rclone client
rclone_client = RcloneClient(RCLONE_RC_URL, RCLONE_RC_USER, RCLONE_RC_PASS)

# Pydantic models for request/response
class MountRequest(BaseModel):
    fs: str
    mount_point: str

class UnmountRequest(BaseModel):
    mount_point: str

class FileOperationRequest(BaseModel):
    src_fs: str = None
    src_remote: str = None
    dst_fs: str = None
    dst_remote: str = None
    fs: str = None
    remote: str = None

# API Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        rclone_client.health_check()
        return {"status": "ok", "rclone_connected": True}
    except Exception:
        return {"status": "error", "rclone_connected": False}

@app.get("/api/remotes")
async def list_remotes():
    """List all configured remotes"""
    try:
        remotes = rclone_client.list_remotes()
        return remotes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/files")
async def list_files(fs: str = Query(...), remote: str = Query("")):
    """List files in a remote"""
    try:
        files = rclone_client.list_files(fs, remote)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config")
async def get_config():
    """Get configuration dump"""
    try:
        config = rclone_client.get_config_dump()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs")
async def list_jobs():
    """List running jobs"""
    try:
        jobs = rclone_client.list_jobs()
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mounts")
async def list_mounts():
    """List active mounts"""
    try:
        mounts = rclone_client.list_mounts()
        return mounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mount")
async def create_mount(request: MountRequest):
    """Create a new mount"""
    try:
        result = rclone_client.create_mount(request.fs, request.mount_point)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/unmount")
async def unmount(request: UnmountRequest):
    """Unmount a mount point"""
    try:
        result = rclone_client.unmount(request.mount_point)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/copy")
async def copy_file(request: FileOperationRequest):
    """Copy a file"""
    try:
        result = rclone_client.copy_file(
            request.src_fs, request.src_remote,
            request.dst_fs, request.dst_remote
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/move")
async def move_file(request: FileOperationRequest):
    """Move a file"""
    try:
        result = rclone_client.move_file(
            request.src_fs, request.src_remote,
            request.dst_fs, request.dst_remote
        )
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/delete")
async def delete_file(request: FileOperationRequest):
    """Delete a file"""
    try:
        result = rclone_client.delete_file(request.fs, request.remote)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/mkdir")
async def create_directory(request: FileOperationRequest):
    """Create a directory"""
    try:
        result = rclone_client.create_directory(request.fs, request.remote)
        return {"status": "success", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Single-page HTML application
@app.get("/", response_class=HTMLResponse)
async def get_index():
    """Serve the single-page application"""
    html_content = """
<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Rclone Web GUI</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }

        .header {
            background: #2563eb;
            color: white;
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .header h1 {
            font-size: 1.5rem;
            font-weight: 600;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem;
        }

        .nav {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
            overflow: hidden;
        }

        .nav-tabs {
            display: flex;
            list-style: none;
        }

        .nav-tab {
            padding: 1rem 1.5rem;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            transition: all 0.2s;
        }

        .nav-tab.active {
            background: #f8fafc;
            border-bottom-color: #2563eb;
            color: #2563eb;
            font-weight: 600;
        }

        .nav-tab:hover {
            background: #f8fafc;
        }

        .content {
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            padding: 2rem;
        }

        .status-card {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }

        .card {
            background: white;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }

        .card h3 {
            font-size: 1.125rem;
            font-weight: 600;
            margin-bottom: 0.5rem;
            color: #374151;
        }

        .status-indicator {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.875rem;
            font-weight: 500;
        }

        .status-online {
            background: #dcfce7;
            color: #166534;
        }

        .status-offline {
            background: #fef2f2;
            color: #991b1b;
        }

        .select {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 1rem;
            background: white;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.75rem 1.5rem;
            border: none;
            border-radius: 6px;
            font-size: 0.875rem;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            text-decoration: none;
        }

        .btn-primary {
            background: #2563eb;
            color: white;
        }

        .btn-primary:hover {
            background: #1d4ed8;
        }

        .btn-secondary {
            background: #f3f4f6;
            color: #374151;
        }

        .btn-secondary:hover {
            background: #e5e7eb;
        }

        .btn-danger {
            background: #dc2626;
            color: white;
        }

        .btn-danger:hover {
            background: #b91c1c;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        .table th,
        .table td {
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }

        .table th {
            background: #f9fafb;
            font-weight: 600;
            color: #374151;
        }

        .breadcrumb {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 1rem;
            font-size: 0.875rem;
            color: #6b7280;
        }

        .breadcrumb a {
            color: #2563eb;
            text-decoration: none;
        }

        .breadcrumb a:hover {
            text-decoration: underline;
        }

        .loading {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            color: #6b7280;
        }

        .spinner {
            width: 1rem;
            height: 1rem;
            border: 2px solid #e5e7eb;
            border-top: 2px solid #2563eb;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .alert {
            padding: 1rem;
            border-radius: 6px;
            margin-bottom: 1rem;
        }

        .alert-error {
            background: #fef2f2;
            border: 1px solid #fecaca;
            color: #991b1b;
        }

        .alert-success {
            background: #f0fdf4;
            border: 1px solid #bbf7d0;
            color: #166534;
        }

        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
            align-items: center;
            justify-content: center;
        }

        .modal.show {
            display: flex;
        }

        .modal-content {
            background: white;
            border-radius: 8px;
            padding: 2rem;
            width: 90%;
            max-width: 500px;
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }

        .modal-title {
            font-size: 1.25rem;
            font-weight: 600;
        }

        .close {
            background: none;
            border: none;
            font-size: 1.5rem;
            cursor: pointer;
            color: #6b7280;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
            color: #374151;
        }

        .form-input {
            width: 100%;
            padding: 0.75rem;
            border: 1px solid #d1d5db;
            border-radius: 6px;
            font-size: 1rem;
        }

        .form-actions {
            display: flex;
            gap: 1rem;
            justify-content: flex-end;
            margin-top: 1.5rem;
        }

        .hidden {
            display: none;
        }

        @media (max-width: 768px) {
            .container {
                padding: 1rem;
            }

            .nav-tabs {
                flex-direction: column;
            }

            .status-card {
                grid-template-columns: 1fr;
            }

            .table {
                font-size: 0.875rem;
            }
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>Rclone Web GUI</h1>
    </div>

    <div class="container">
        <nav class="nav">
            <ul class="nav-tabs">
                <li class="nav-tab active" onclick="showTab('dashboard')">Dashboard</li>
                <li class="nav-tab" onclick="showTab('explorer')">File Explorer</li>
                <li class="nav-tab" onclick="showTab('remotes')">Remotes</li>
                <li class="nav-tab" onclick="showTab('mounts')">Mounts</li>
            </ul>
        </nav>

        <div id="dashboard" class="content">
            <h2>Dashboard</h2>
            <div id="dashboard-content">
                <div class="loading">
                    <div class="spinner"></div>
                    Loading dashboard...
                </div>
            </div>
        </div>

        <div id="explorer" class="content hidden">
            <h2>File Explorer</h2>
            <div id="explorer-content">
                <div class="form-group">
                    <label class="form-label">Select Remote:</label>
                    <select id="remote-select" class="select" onchange="loadFiles()">
                        <option value="">Select a remote...</option>
                    </select>
                </div>
                <div id="explorer-actions" class="hidden">
                    <button class="btn btn-primary" onclick="showCreateDirModal()">
                        <span>+</span> New Folder
                    </button>
                </div>
                <div id="breadcrumb" class="breadcrumb hidden"></div>
                <div id="files-list"></div>
            </div>
        </div>

        <div id="remotes" class="content hidden">
            <h2>Remotes</h2>
            <div id="remotes-content">
                <div class="loading">
                    <div class="spinner"></div>
                    Loading remotes...
                </div>
            </div>
        </div>

        <div id="mounts" class="content hidden">
            <h2>Mounts</h2>
            <div id="mounts-content">
                <div style="margin-bottom: 1rem;">
                    <button class="btn btn-primary" onclick="showCreateMountModal()">
                        <span>+</span> Create Mount
                    </button>
                </div>
                <div id="mounts-list">
                    <div class="loading">
                        <div class="spinner"></div>
                        Loading mounts...
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- Modals -->
    <div id="create-dir-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">Create New Directory</h3>
                <button class="close" onclick="hideCreateDirModal()">&times;</button>
            </div>
            <div class="form-group">
                <label class="form-label">Directory Name:</label>
                <input type="text" id="dir-name" class="form-input" placeholder="Enter directory name">
            </div>
            <div class="form-actions">
                <button class="btn btn-secondary" onclick="hideCreateDirModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createDirectory()">Create</button>
            </div>
        </div>
    </div>

    <div id="create-mount-modal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">Create New Mount</h3>
                <button class="close" onclick="hideCreateMountModal()">&times;</button>
            </div>
            <div class="form-group">
                <label class="form-label">Remote:</label>
                <select id="mount-remote-select" class="form-input">
                    <option value="">Select a remote...</option>
                </select>
            </div>
            <div class="form-group">
                <label class="form-label">Mount Point:</label>
                <input type="text" id="mount-point" class="form-input" placeholder="/mnt/rclone">
            </div>
            <div class="form-actions">
                <button class="btn btn-secondary" onclick="hideCreateMountModal()">Cancel</button>
                <button class="btn btn-primary" onclick="createMount()">Create Mount</button>
            </div>
        </div>
    </div>

    <script>
        // Global state
        let currentRemote = '';
        let currentPath = [];
        let allRemotes = [];

        // Tab switching
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.content').forEach(tab => {
                tab.classList.add('hidden');
            });

            // Remove active class from all nav tabs
            document.querySelectorAll('.nav-tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName).classList.remove('hidden');
            event.target.classList.add('active');

            // Load data for the tab
            switch(tabName) {
                case 'dashboard':
                    loadDashboard();
                    break;
                case 'explorer':
                    loadRemotes();
                    break;
                case 'remotes':
                    loadRemotesConfig();
                    break;
                case 'mounts':
                    loadMounts();
                    break;
            }
        }

        // API helper
        async function apiCall(endpoint, method = 'GET', data = null) {
            const config = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                }
            };

            if (data) {
                config.body = JSON.stringify(data);
            }

            const response = await fetch(`/api/${endpoint}`, config);
            if (!response.ok) {
                throw new Error(`API call failed: ${response.statusText}`);
            }
            return await response.json();
        }

        // Dashboard
        async function loadDashboard() {
            const content = document.getElementById('dashboard-content');
            content.innerHTML = '<div class="loading"><div class="spinner"></div> Loading dashboard...</div>';

            try {
                const [health, mounts, jobs] = await Promise.all([
                    fetch('/health').then(r => r.json()),
                    apiCall('mounts'),
                    apiCall('jobs')
                ]);

                content.innerHTML = `
                    <div class="status-card">
                        <div class="card">
                            <h3>Rclone Status</h3>
                            <span class="status-indicator ${health.rclone_connected ? 'status-online' : 'status-offline'}">
                                ${health.rclone_connected ? '● Online' : '● Offline'}
                            </span>
                        </div>
                        <div class="card">
                            <h3>Active Mounts</h3>
                            <p>${mounts.length} mount(s)</p>
                        </div>
                        <div class="card">
                            <h3>Running Jobs</h3>
                            <p>${jobs.length} job(s)</p>
                        </div>
                    </div>
                `;
            } catch (error) {
                content.innerHTML = `<div class="alert alert-error">Error loading dashboard: ${error.message}</div>`;
            }
        }

        // File Explorer
        async function loadRemotes() {
            try {
                allRemotes = await apiCall('remotes');
                const select = document.getElementById('remote-select');
                select.innerHTML = '<option value="">Select a remote...</option>';

                allRemotes.forEach(remote => {
                    const option = document.createElement('option');
                    option.value = remote;
                    option.textContent = remote;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Error loading remotes:', error);
            }
        }

        async function loadFiles() {
            const remote = document.getElementById('remote-select').value;
            if (!remote) {
                document.getElementById('explorer-actions').classList.add('hidden');
                document.getElementById('breadcrumb').classList.add('hidden');
                document.getElementById('files-list').innerHTML = '';
                return;
            }

            currentRemote = remote;
            currentPath = [];
            await loadFilesForPath();
            document.getElementById('explorer-actions').classList.remove('hidden');
        }

        async function loadFilesForPath() {
            const content = document.getElementById('files-list');
            content.innerHTML = '<div class="loading"><div class="spinner"></div> Loading files...</div>';

            try {
                const path = currentPath.join('/');
                const files = await apiCall(`files?fs=${encodeURIComponent(currentRemote)}&remote=${encodeURIComponent(path)}`);

                // Update breadcrumb
                updateBreadcrumb();

                // Render files
                if (files.length === 0) {
                    content.innerHTML = '<p>No files found.</p>';
                    return;
                }

                const table = document.createElement('table');
                table.className = 'table';

                const header = table.createTHead();
                const headerRow = header.insertRow();
                ['Name', 'Size', 'Type', 'Actions'].forEach(text => {
                    const th = document.createElement('th');
                    th.textContent = text;
                    headerRow.appendChild(th);
                });

                const tbody = table.createTBody();
                files.forEach(file => {
                    const row = tbody.insertRow();

                    // Name
                    const nameCell = row.insertCell();
                    const icon = file.is_dir ? '📁' : '📄';
                    if (file.is_dir) {
                        const link = document.createElement('a');
                        link.href = '#';
                        link.textContent = file.name;
                        link.onclick = () => navigateToDirectory(file.name);
                        nameCell.appendChild(document.createTextNode(icon + ' '));
                        nameCell.appendChild(link);
                    } else {
                        nameCell.textContent = icon + ' ' + file.name;
                    }

                    // Size
                    const sizeCell = row.insertCell();
                    sizeCell.textContent = file.size ? formatFileSize(file.size) : '-';

                    // Type
                    const typeCell = row.insertCell();
                    typeCell.textContent = file.is_dir ? 'Directory' : 'File';

                    // Actions
                    const actionsCell = row.insertCell();
                    actionsCell.innerHTML = '<button class="btn btn-danger btn-sm">Delete</button>';
                });

                content.innerHTML = '';
                content.appendChild(table);

            } catch (error) {
                content.innerHTML = `<div class="alert alert-error">Error loading files: ${error.message}</div>`;
            }
        }

        function updateBreadcrumb() {
            const breadcrumb = document.getElementById('breadcrumb');
            breadcrumb.classList.remove('hidden');

            const parts = [currentRemote, ...currentPath];
            breadcrumb.innerHTML = '';

            parts.forEach((part, index) => {
                if (index > 0) {
                    breadcrumb.appendChild(document.createTextNode(' / '));
                }

                if (index === parts.length - 1) {
                    breadcrumb.appendChild(document.createTextNode(part));
                } else {
                    const link = document.createElement('a');
                    link.href = '#';
                    link.textContent = part;
                    link.onclick = () => navigateToPath(index);
                    breadcrumb.appendChild(link);
                }
            });

            // Add back button if not at root
            if (currentPath.length > 0) {
                const backBtn = document.createElement('button');
                backBtn.className = 'btn btn-secondary';
                backBtn.textContent = '← Back';
                backBtn.onclick = () => navigateToPath(currentPath.length - 1);
                backBtn.style.marginLeft = '1rem';
                breadcrumb.appendChild(backBtn);
            }
        }

        function navigateToDirectory(dirName) {
            currentPath.push(dirName);
            loadFilesForPath();
        }

        function navigateToPath(level) {
            currentPath = currentPath.slice(0, level);
            loadFilesForPath();
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
        }

        // Modals
        function showCreateDirModal() {
            document.getElementById('create-dir-modal').classList.add('show');
            document.getElementById('dir-name').focus();
        }

        function hideCreateDirModal() {
            document.getElementById('create-dir-modal').classList.remove('show');
            document.getElementById('dir-name').value = '';
        }

        async function createDirectory() {
            const dirName = document.getElementById('dir-name').value.trim();
            if (!dirName) return;

            try {
                const path = currentPath.length > 0 ? currentPath.join('/') + '/' + dirName : dirName;
                await apiCall('mkdir', 'POST', {
                    fs: currentRemote,
                    remote: path
                });

                hideCreateDirModal();
                loadFilesForPath();
                showAlert('Directory created successfully!', 'success');
            } catch (error) {
                showAlert(`Error creating directory: ${error.message}`, 'error');
            }
        }

        function showCreateMountModal() {
            const select = document.getElementById('mount-remote-select');
            select.innerHTML = '<option value="">Select a remote...</option>';

            allRemotes.forEach(remote => {
                const option = document.createElement('option');
                option.value = remote;
                option.textContent = remote;
                select.appendChild(option);
            });

            document.getElementById('create-mount-modal').classList.add('show');
        }

        function hideCreateMountModal() {
            document.getElementById('create-mount-modal').classList.remove('show');
            document.getElementById('mount-remote-select').value = '';
            document.getElementById('mount-point').value = '';
        }

        async function createMount() {
            const remote = document.getElementById('mount-remote-select').value;
            const mountPoint = document.getElementById('mount-point').value.trim();

            if (!remote || !mountPoint) {
                showAlert('Please fill in all fields', 'error');
                return;
            }

            try {
                await apiCall('mount', 'POST', {
                    fs: remote,
                    mount_point: mountPoint
                });

                hideCreateMountModal();
                loadMounts();
                showAlert('Mount created successfully!', 'success');
            } catch (error) {
                showAlert(`Error creating mount: ${error.message}`, 'error');
            }
        }

        // Remotes
        async function loadRemotesConfig() {
            const content = document.getElementById('remotes-content');
            content.innerHTML = '<div class="loading"><div class="spinner"></div> Loading remotes...</div>';

            try {
                const config = await apiCall('config');

                if (Object.keys(config).length === 0) {
                    content.innerHTML = '<p>No remotes configured.</p>';
                    return;
                }

                const cards = Object.entries(config).map(([name, cfg]) => `
                    <div class="card">
                        <h3>${name}</h3>
                        <p><strong>Type:</strong> ${cfg.type || 'Unknown'}</p>
                        ${cfg.path ? `<p><strong>Path:</strong> ${cfg.path}</p>` : ''}
                    </div>
                `).join('');

                content.innerHTML = `<div class="status-card">${cards}</div>`;

            } catch (error) {
                content.innerHTML = `<div class="alert alert-error">Error loading remotes: ${error.message}</div>`;
            }
        }

        // Mounts
        async function loadMounts() {
            const content = document.getElementById('mounts-list');
            content.innerHTML = '<div class="loading"><div class="spinner"></div> Loading mounts...</div>';

            try {
                const mounts = await apiCall('mounts');

                if (mounts.length === 0) {
                    content.innerHTML = '<p>No active mounts.</p>';
                    return;
                }

                const cards = mounts.map(mount => `
                    <div class="card">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h3>${mount.mount_point}</h3>
                                <p>Active mount</p>
                            </div>
                            <button class="btn btn-danger" onclick="unmount('${mount.mount_point}')">
                                Unmount
                            </button>
                        </div>
                    </div>
                `).join('');

                content.innerHTML = `<div class="status-card">${cards}</div>`;

            } catch (error) {
                content.innerHTML = `<div class="alert alert-error">Error loading mounts: ${error.message}</div>`;
            }
        }

        async function unmount(mountPoint) {
            try {
                await apiCall('unmount', 'POST', { mount_point: mountPoint });
                loadMounts();
                showAlert('Mount removed successfully!', 'success');
            } catch (error) {
                showAlert(`Error removing mount: ${error.message}`, 'error');
            }
        }

        // Utilities
        function showAlert(message, type) {
            const alert = document.createElement('div');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;

            const container = document.querySelector('.container');
            container.insertBefore(alert, container.firstChild);

            setTimeout(() => {
                alert.remove();
            }, 5000);
        }

        // Initialize
        document.addEventListener('DOMContentLoaded', function() {
            loadDashboard();
            loadRemotes();
        });
    </script>
</body>
</html>
"""
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Rclone Web GUI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--rclone-url", default="http://localhost:5572", help="Rclone RC URL")
    parser.add_argument("--rclone-user", default="admin", help="Rclone RC username")
    parser.add_argument("--rclone-pass", default="secret", help="Rclone RC password")

    args = parser.parse_args()

    # Override environment variables with command line args
    os.environ["RCLONE_RC_URL"] = args.rclone_url
    os.environ["RCLONE_RC_USER"] = args.rclone_user
    os.environ["RCLONE_RC_PASS"] = args.rclone_pass

    print("🚀 Starting Rclone Web GUI (Python)...")
    print(f"📱 Web interface: http://{args.host}:{args.port}")
    print(f"🔗 Rclone RC URL: {args.rclone_url}")
    print("Press Ctrl+C to stop")

    uvicorn.run(app, host=args.host, port=args.port)
