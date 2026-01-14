use axum::{
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use clap::Parser;
use serde::{Deserialize, Serialize};
use std::net::SocketAddr;
use tower_http::cors::CorsLayer;

mod rclone_api;
mod handlers;

use handlers::*;

#[derive(Parser)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Address to bind the server to
    #[arg(short, long, default_value = "127.0.0.1:3001")]
    bind: String,

    /// Rclone RC server address
    #[arg(short, long, default_value = "http://localhost:5572")]
    rclone_url: String,

    /// Username for rclone RC auth
    #[arg(short, long)]
    username: Option<String>,

    /// Password for rclone RC auth
    #[arg(short = 'P', long)]
    password: Option<String>,
}

#[derive(Serialize)]
struct HealthResponse {
    status: String,
    rclone_connected: bool,
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let args = Args::parse();

    // Create rclone API client
    let rclone_client = rclone_api::RcloneClient::new(
        &args.rclone_url,
        args.username.as_deref(),
        args.password.as_deref(),
    );

    // Build our application with routes
    let app = Router::new()
        .route("/health", get(health_check))
        .route("/api/remotes", get(list_remotes))
        .route("/api/files", get(list_files))
        .route("/api/config", get(get_config))
        .route("/api/jobs", get(list_jobs))
        .route("/api/mounts", get(list_mounts))
        .route("/api/mount", post(create_mount))
        .route("/api/unmount", post(unmount))
        .route("/api/copy", post(copy_file))
        .route("/api/move", post(move_file))
        .route("/api/delete", post(delete_file))
        .route("/api/mkdir", post(create_directory))
        .layer(CorsLayer::permissive())
        .with_state(rclone_client);

    // Parse bind address
    let addr: SocketAddr = args.bind.parse().expect("Invalid bind address");

    tracing::info!("Starting server on {}", addr);
    tracing::info!("Rclone RC URL: {}", args.rclone_url);

    let listener = tokio::net::TcpListener::bind(addr).await.unwrap();
    axum::serve(listener, app).await.unwrap();
}

async fn health_check(
    axum::extract::State(client): axum::extract::State<rclone_api::RcloneClient>,
) -> Result<Json<HealthResponse>, StatusCode> {
    let connected = client.health_check().await.is_ok();

    Ok(Json(HealthResponse {
        status: "ok".to_string(),
        rclone_connected: connected,
    }))
}
