import { useEffect, useState } from 'react'
import {
  Container,
  Title,
  Select,
  Button,
  Group,
  Table,
  Text,
  Loader,
  Alert,
  ActionIcon,
  Breadcrumbs,
  Anchor,
  Modal,
  TextInput,
  Stack,
} from '@mantine/core'
import {
  IconFolder,
  IconFile,
  IconArrowLeft,
  IconPlus,
  IconTrash,
  IconCopy,
  IconArrowsRight,
  IconX
} from '@tabler/icons-react'
import { apiService } from '../services/api'
import { FileInfo } from '../types/api'
import { notifications } from '@mantine/notifications'

function FileExplorer() {
  const [remotes, setRemotes] = useState<string[]>([])
  const [selectedRemote, setSelectedRemote] = useState<string>('')
  const [currentPath, setCurrentPath] = useState<string[]>([])
  const [files, setFiles] = useState<FileInfo[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Modal states
  const [createDirModal, setCreateDirModal] = useState(false)
  const [newDirName, setNewDirName] = useState('')

  useEffect(() => {
    loadRemotes()
  }, [])

  useEffect(() => {
    if (selectedRemote) {
      loadFiles()
    }
  }, [selectedRemote, currentPath])

  const loadRemotes = async () => {
    try {
      const remotesData = await apiService.listRemotes()
      setRemotes(remotesData)
    } catch (err) {
      setError('Failed to load remotes')
      console.error('Load remotes error:', err)
    }
  }

  const loadFiles = async () => {
    if (!selectedRemote) return

    setLoading(true)
    try {
      const path = currentPath.length > 0 ? currentPath.join('/') : ''
      const filesData = await apiService.listFiles({
        fs: selectedRemote,
        remote: path,
      })
      setFiles(filesData)
      setError(null)
    } catch (err) {
      setError('Failed to load files')
      console.error('Load files error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleRemoteChange = (remote: string) => {
    setSelectedRemote(remote)
    setCurrentPath([])
  }

  const handleNavigate = (path: string) => {
    const newPath = [...currentPath, path]
    setCurrentPath(newPath)
  }

  const handleGoBack = () => {
    if (currentPath.length > 0) {
      setCurrentPath(currentPath.slice(0, -1))
    }
  }

  const handleBreadcrumbClick = (index: number) => {
    setCurrentPath(currentPath.slice(0, index + 1))
  }

  const handleCreateDirectory = async () => {
    if (!newDirName.trim()) return

    try {
      const path = currentPath.length > 0 ? currentPath.join('/') + '/' : ''
      await apiService.createDirectory({
        fs: selectedRemote,
        remote: path + newDirName,
      })

      setCreateDirModal(false)
      setNewDirName('')
      loadFiles()
      notifications.show({
        title: 'Success',
        message: 'Directory created successfully',
        color: 'green',
      })
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to create directory',
        color: 'red',
      })
      console.error('Create directory error:', err)
    }
  }

  const formatFileSize = (size?: number) => {
    if (!size) return '-'
    const units = ['B', 'KB', 'MB', 'GB', 'TB']
    let unitIndex = 0
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024
      unitIndex++
    }
    return `${size.toFixed(1)} ${units[unitIndex]}`
  }

  const breadcrumbs = [
    { title: selectedRemote, href: '#' },
    ...currentPath.map((part, index) => ({
      title: part,
      href: '#',
      index,
    })),
  ]

  return (
    <Container size="xl">
      <Title order={2} mb="xl">File Explorer</Title>

      <Stack spacing="md">
        {/* Remote Selector */}
        <Group>
          <Select
            label="Remote"
            placeholder="Select a remote"
            data={remotes}
            value={selectedRemote}
            onChange={handleRemoteChange}
            style={{ flex: 1 }}
          />
        </Group>

        {selectedRemote && (
          <>
            {/* Navigation */}
            <Group>
              <Button
                leftIcon={<IconArrowLeft size="1rem" />}
                onClick={handleGoBack}
                disabled={currentPath.length === 0}
                variant="light"
              >
                Back
              </Button>

              <Button
                leftIcon={<IconPlus size="1rem" />}
                onClick={() => setCreateDirModal(true)}
                variant="light"
              >
                New Folder
              </Button>
            </Group>

            {/* Breadcrumbs */}
            <Breadcrumbs>
              {breadcrumbs.map((item, index) => (
                <Anchor
                  key={index}
                  onClick={() => handleBreadcrumbClick(index)}
                  style={{ cursor: 'pointer' }}
                >
                  {item.title}
                </Anchor>
              ))}
            </Breadcrumbs>

            {/* Files Table */}
            {loading ? (
              <Group position="center" mt="xl">
                <Loader size="lg" />
              </Group>
            ) : error ? (
              <Alert icon={<IconX size="1rem" />} title="Error" color="red">
                {error}
              </Alert>
            ) : (
              <Table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Size</th>
                    <th>Type</th>
                    <th>Modified</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {files.map((file) => (
                    <tr key={file.path}>
                      <td>
                        <Group spacing="xs">
                          {file.is_dir ? (
                            <IconFolder size="1rem" />
                          ) : (
                            <IconFile size="1rem" />
                          )}
                          {file.is_dir ? (
                            <Anchor
                              onClick={() => handleNavigate(file.name)}
                              style={{ cursor: 'pointer' }}
                            >
                              {file.name}
                            </Anchor>
                          ) : (
                            <Text>{file.name}</Text>
                          )}
                        </Group>
                      </td>
                      <td>{formatFileSize(file.size)}</td>
                      <td>{file.is_dir ? 'Directory' : 'File'}</td>
                      <td>
                        {file.mod_time
                          ? new Date(file.mod_time).toLocaleString()
                          : '-'
                        }
                      </td>
                      <td>
                        <Group spacing="xs">
                          <ActionIcon variant="light" color="blue">
                            <IconCopy size="1rem" />
                          </ActionIcon>
                          <ActionIcon variant="light" color="green">
                            <IconArrowsRight size="1rem" />
                          </ActionIcon>
                          <ActionIcon variant="light" color="red">
                            <IconTrash size="1rem" />
                          </ActionIcon>
                        </Group>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            )}
          </>
        )}
      </Stack>

      {/* Create Directory Modal */}
      <Modal
        opened={createDirModal}
        onClose={() => setCreateDirModal(false)}
        title="Create New Directory"
      >
        <Stack>
          <TextInput
            label="Directory Name"
            value={newDirName}
            onChange={(event) => setNewDirName(event.currentTarget.value)}
            placeholder="Enter directory name"
          />
          <Group position="right">
            <Button variant="light" onClick={() => setCreateDirModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateDirectory}>
              Create
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}

export default FileExplorer
