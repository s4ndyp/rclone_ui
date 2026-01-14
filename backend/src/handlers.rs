use axum::{
    extract::{Query, State},
    http::StatusCode,
    response::Json,
    Form,
};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

use crate::rclone_api::{RcloneClient, FileInfo, JobInfo, MountInfo};

// List remotes
pub async fn list_remotes(
    State(client): State<RcloneClient>,
) -> Result<Json<Vec<String>>, StatusCode> {
    match client.list_remotes().await {
        Ok(remotes) => Ok(Json(remotes)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// List files
#[derive(Deserialize)]
pub struct ListFilesQuery {
    fs: String,
    remote: Option<String>,
}

pub async fn list_files(
    State(client): State<RcloneClient>,
    Query(params): Query<ListFilesQuery>,
) -> Result<Json<Vec<FileInfo>>, StatusCode> {
    let remote = params.remote.unwrap_or_else(|| "".to_string());
    match client.list_files(&params.fs, &remote).await {
        Ok(files) => Ok(Json(files)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Get config dump
pub async fn get_config(
    State(client): State<RcloneClient>,
) -> Result<Json<HashMap<String, serde_json::Value>>, StatusCode> {
    match client.get_config_dump().await {
        Ok(config) => Ok(Json(config)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// List jobs
pub async fn list_jobs(
    State(client): State<RcloneClient>,
) -> Result<Json<Vec<JobInfo>>, StatusCode> {
    match client.list_jobs().await {
        Ok(jobs) => Ok(Json(jobs)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// List mounts
pub async fn list_mounts(
    State(client): State<RcloneClient>,
) -> Result<Json<Vec<MountInfo>>, StatusCode> {
    match client.list_mounts().await {
        Ok(mounts) => Ok(Json(mounts)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Create mount
#[derive(Deserialize)]
pub struct CreateMountRequest {
    fs: String,
    mount_point: String,
}

pub async fn create_mount(
    State(client): State<RcloneClient>,
    Json(payload): Json<CreateMountRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.create_mount(&payload.fs, &payload.mount_point).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Unmount
#[derive(Deserialize)]
pub struct UnmountRequest {
    mount_point: String,
}

pub async fn unmount(
    State(client): State<RcloneClient>,
    Json(payload): Json<UnmountRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.unmount(&payload.mount_point).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Copy file
#[derive(Deserialize)]
pub struct CopyFileRequest {
    src_fs: String,
    src_remote: String,
    dst_fs: String,
    dst_remote: String,
}

pub async fn copy_file(
    State(client): State<RcloneClient>,
    Json(payload): Json<CopyFileRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.copy_file(&payload.src_fs, &payload.src_remote, &payload.dst_fs, &payload.dst_remote).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Move file
#[derive(Deserialize)]
pub struct MoveFileRequest {
    src_fs: String,
    src_remote: String,
    dst_fs: String,
    dst_remote: String,
}

pub async fn move_file(
    State(client): State<RcloneClient>,
    Json(payload): Json<MoveFileRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.move_file(&payload.src_fs, &payload.src_remote, &payload.dst_fs, &payload.dst_remote).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Delete file
#[derive(Deserialize)]
pub struct DeleteFileRequest {
    fs: String,
    remote: String,
}

pub async fn delete_file(
    State(client): State<RcloneClient>,
    Json(payload): Json<DeleteFileRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.delete_file(&payload.fs, &payload.remote).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

// Create directory
#[derive(Deserialize)]
pub struct CreateDirectoryRequest {
    fs: String,
    remote: String,
}

pub async fn create_directory(
    State(client): State<RcloneClient>,
    Json(payload): Json<CreateDirectoryRequest>,
) -> Result<StatusCode, StatusCode> {
    match client.create_directory(&payload.fs, &payload.remote).await {
        Ok(_) => Ok(StatusCode::OK),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}
