export interface FileInfo {
  path: string
  name: string
  size?: number
  is_dir: boolean
  mod_time?: string
}

export interface JobInfo {
  id: number
}

export interface MountInfo {
  mount_point: string
}

export interface HealthResponse {
  status: string
  rclone_connected: boolean
}

export interface ListFilesParams {
  fs: string
  remote?: string
}

export interface CopyFileRequest {
  src_fs: string
  src_remote: string
  dst_fs: string
  dst_remote: string
}

export interface MoveFileRequest {
  src_fs: string
  src_remote: string
  dst_fs: string
  dst_remote: string
}

export interface DeleteFileRequest {
  fs: string
  remote: string
}

export interface CreateDirectoryRequest {
  fs: string
  remote: string
}

export interface CreateMountRequest {
  fs: string
  mount_point: string
}

export interface UnmountRequest {
  mount_point: string
}
