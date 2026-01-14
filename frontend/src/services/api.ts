import axios from 'axios'
import {
  FileInfo,
  JobInfo,
  MountInfo,
  HealthResponse,
  ListFilesParams,
  CopyFileRequest,
  MoveFileRequest,
  DeleteFileRequest,
  CreateDirectoryRequest,
  CreateMountRequest,
  UnmountRequest
} from '../types/api'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export const apiService = {
  // Health check
  async healthCheck(): Promise<HealthResponse> {
    const response = await api.get('/health')
    return response.data
  },

  // Remotes
  async listRemotes(): Promise<string[]> {
    const response = await api.get('/remotes')
    return response.data
  },

  // Files
  async listFiles(params: ListFilesParams): Promise<FileInfo[]> {
    const response = await api.get('/files', { params })
    return response.data
  },

  // Config
  async getConfig(): Promise<Record<string, any>> {
    const response = await api.get('/config')
    return response.data
  },

  // Jobs
  async listJobs(): Promise<JobInfo[]> {
    const response = await api.get('/jobs')
    return response.data
  },

  // Mounts
  async listMounts(): Promise<MountInfo[]> {
    const response = await api.get('/mounts')
    return response.data
  },

  async createMount(data: CreateMountRequest): Promise<void> {
    await api.post('/mount', data)
  },

  async unmount(data: UnmountRequest): Promise<void> {
    await api.post('/unmount', data)
  },

  // File operations
  async copyFile(data: CopyFileRequest): Promise<void> {
    await api.post('/copy', data)
  },

  async moveFile(data: MoveFileRequest): Promise<void> {
    await api.post('/move', data)
  },

  async deleteFile(data: DeleteFileRequest): Promise<void> {
    await api.post('/delete', data)
  },

  async createDirectory(data: CreateDirectoryRequest): Promise<void> {
    await api.post('/mkdir', data)
  },
}
