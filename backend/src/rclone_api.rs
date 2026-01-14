use reqwest::Client;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use base64::{Engine as _, engine::general_purpose};

#[derive(Clone)]
pub struct RcloneClient {
    client: Client,
    base_url: String,
    auth_header: Option<String>,
}

impl RcloneClient {
    pub fn new(base_url: &str, username: Option<&str>, password: Option<&str>) -> Self {
        let mut headers = reqwest::header::HeaderMap::new();
        headers.insert("Content-Type", "application/json".parse().unwrap());

        let auth_header = if let (Some(user), Some(pass)) = (username, password) {
            let credentials = format!("{}:{}", user, pass);
            let encoded = general_purpose::STANDARD.encode(credentials);
            Some(format!("Basic {}", encoded))
        } else {
            None
        };

        let client = Client::builder()
            .default_headers(headers)
            .build()
            .expect("Failed to create HTTP client");

        Self {
            client,
            base_url: base_url.trim_end_matches('/').to_string(),
            auth_header,
        }
    }

    async fn make_request<T: for<'de> Deserialize<'de>>(
        &self,
        endpoint: &str,
        body: Option<serde_json::Value>,
    ) -> Result<T, Box<dyn std::error::Error>> {
        let url = format!("{}/{}", self.base_url, endpoint);

        let mut request = match body {
            Some(data) => self.client.post(&url).json(&data),
            None => self.client.post(&url),
        };

        if let Some(auth) = &self.auth_header {
            request = request.header("Authorization", auth);
        }

        let response = request.send().await?;
        let status = response.status();

        if !status.is_success() {
            let error_text = response.text().await.unwrap_or_default();
            return Err(format!("HTTP {}: {}", status, error_text).into());
        }

        let result = response.json::<T>().await?;
        Ok(result)
    }

    pub async fn health_check(&self) -> Result<(), Box<dyn std::error::Error>> {
        let _: serde_json::Value = self.make_request("rc/noopauth", None).await?;
        Ok(())
    }

    pub async fn list_remotes(&self) -> Result<Vec<String>, Box<dyn std::error::Error>> {
        #[derive(Deserialize)]
        struct Response {
            remotes: Vec<String>,
        }

        let response: Response = self.make_request("config/listremotes", None).await?;
        Ok(response.remotes)
    }

    pub async fn list_files(&self, fs: &str, remote: &str) -> Result<Vec<FileInfo>, Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            fs: String,
            remote: String,
        }

        #[derive(Deserialize)]
        struct Response {
            list: Vec<FileInfo>,
        }

        let request = Request {
            fs: fs.to_string(),
            remote: remote.to_string(),
        };

        let response: Response = self.make_request("operations/list", Some(serde_json::to_value(request)?)).await?;
        Ok(response.list)
    }

    pub async fn get_config_dump(&self) -> Result<HashMap<String, serde_json::Value>, Box<dyn std::error::Error>> {
        let response: HashMap<String, serde_json::Value> = self.make_request("config/dump", None).await?;
        Ok(response)
    }

    pub async fn list_jobs(&self) -> Result<Vec<JobInfo>, Box<dyn std::error::Error>> {
        #[derive(Deserialize)]
        struct Response {
            jobids: Vec<i32>,
        }

        let response: Response = self.make_request("job/list", None).await?;
        Ok(response.jobids.into_iter().map(|id| JobInfo { id }).collect())
    }

    pub async fn list_mounts(&self) -> Result<Vec<MountInfo>, Box<dyn std::error::Error>> {
        #[derive(Deserialize)]
        struct Response {
            mountPoints: Vec<String>,
        }

        let response: Response = self.make_request("mount/listmounts", None).await?;
        Ok(response.mountPoints.into_iter().map(|point| MountInfo { mount_point: point }).collect())
    }

    pub async fn create_mount(&self, fs: &str, mount_point: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            fs: String,
            mountPoint: String,
        }

        let request = Request {
            fs: fs.to_string(),
            mountPoint: mount_point.to_string(),
        };

        let _: serde_json::Value = self.make_request("mount/mount", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }

    pub async fn unmount(&self, mount_point: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            mountPoint: String,
        }

        let request = Request {
            mountPoint: mount_point.to_string(),
        };

        let _: serde_json::Value = self.make_request("mount/unmount", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }

    pub async fn copy_file(&self, src_fs: &str, src_remote: &str, dst_fs: &str, dst_remote: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            srcFs: String,
            srcRemote: String,
            dstFs: String,
            dstRemote: String,
            _async: bool,
        }

        let request = Request {
            srcFs: src_fs.to_string(),
            srcRemote: src_remote.to_string(),
            dstFs: dst_fs.to_string(),
            dstRemote: dst_remote.to_string(),
            _async: true,
        };

        let _: serde_json::Value = self.make_request("operations/copyfile", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }

    pub async fn move_file(&self, src_fs: &str, src_remote: &str, dst_fs: &str, dst_remote: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            srcFs: String,
            srcRemote: String,
            dstFs: String,
            dstRemote: String,
            _async: bool,
        }

        let request = Request {
            srcFs: src_fs.to_string(),
            srcRemote: src_remote.to_string(),
            dstFs: dst_fs.to_string(),
            dstRemote: dst_remote.to_string(),
            _async: true,
        };

        let _: serde_json::Value = self.make_request("operations/movefile", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }

    pub async fn delete_file(&self, fs: &str, remote: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            fs: String,
            remote: String,
        }

        let request = Request {
            fs: fs.to_string(),
            remote: remote.to_string(),
        };

        let _: serde_json::Value = self.make_request("operations/deletefile", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }

    pub async fn create_directory(&self, fs: &str, remote: &str) -> Result<(), Box<dyn std::error::Error>> {
        #[derive(Serialize)]
        struct Request {
            fs: String,
            remote: String,
        }

        let request = Request {
            fs: fs.to_string(),
            remote: remote.to_string(),
        };

        let _: serde_json::Value = self.make_request("operations/mkdir", Some(serde_json::to_value(request)?)).await?;
        Ok(())
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileInfo {
    pub path: String,
    pub name: String,
    pub size: Option<i64>,
    pub is_dir: bool,
    pub mod_time: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct JobInfo {
    pub id: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MountInfo {
    pub mount_point: String,
}
