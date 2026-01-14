import { useEffect, useState } from 'react'
import {
  Container,
  Title,
  Card,
  Text,
  Loader,
  Alert,
  Group,
  Stack,
  Button,
  Modal,
  Select,
  TextInput,
  ActionIcon,
} from '@mantine/core'
import { IconMount, IconX, IconTrash, IconPlus } from '@tabler/icons-react'
import { apiService } from '../services/api'
import { MountInfo } from '../types/api'
import { notifications } from '@mantine/notifications'

function Mounts() {
  const [mounts, setMounts] = useState<MountInfo[]>([])
  const [remotes, setRemotes] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Modal states
  const [createMountModal, setCreateMountModal] = useState(false)
  const [selectedRemote, setSelectedRemote] = useState('')
  const [mountPoint, setMountPoint] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      const [mountsData, remotesData] = await Promise.all([
        apiService.listMounts(),
        apiService.listRemotes(),
      ])

      setMounts(mountsData)
      setRemotes(remotesData)
    } catch (err) {
      setError('Failed to load mounts data')
      console.error('Load mounts error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleCreateMount = async () => {
    if (!selectedRemote || !mountPoint) return

    try {
      await apiService.createMount({
        fs: selectedRemote,
        mount_point: mountPoint,
      })

      setCreateMountModal(false)
      setSelectedRemote('')
      setMountPoint('')
      loadData()
      notifications.show({
        title: 'Success',
        message: 'Mount created successfully',
        color: 'green',
      })
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to create mount',
        color: 'red',
      })
      console.error('Create mount error:', err)
    }
  }

  const handleUnmount = async (mountPoint: string) => {
    try {
      await apiService.unmount({
        mount_point: mountPoint,
      })

      loadData()
      notifications.show({
        title: 'Success',
        message: 'Mount removed successfully',
        color: 'green',
      })
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to remove mount',
        color: 'red',
      })
      console.error('Unmount error:', err)
    }
  }

  if (loading) {
    return (
      <Container>
        <Group position="center" mt="xl">
          <Loader size="lg" />
        </Group>
      </Container>
    )
  }

  if (error) {
    return (
      <Container>
        <Alert icon={<IconX size="1rem" />} title="Error" color="red">
          {error}
        </Alert>
      </Container>
    )
  }

  return (
    <Container size="xl">
      <Group position="apart" mb="xl">
        <Title order={2}>Mounts</Title>
        <Button
          leftIcon={<IconPlus size="1rem" />}
          onClick={() => setCreateMountModal(true)}
        >
          Create Mount
        </Button>
      </Group>

      <Stack spacing="md">
        {mounts.length === 0 ? (
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text align="center" color="dimmed">
              No active mounts. Click "Create Mount" to mount a remote.
            </Text>
          </Card>
        ) : (
          mounts.map((mount, index) => (
            <Card key={index} shadow="sm" padding="lg" radius="md" withBorder>
              <Group position="apart">
                <Stack spacing="xs">
                  <Text weight={500} size="lg">{mount.mount_point}</Text>
                  <Text size="sm" color="dimmed">
                    Mounted remote filesystem
                  </Text>
                </Stack>

                <Group>
                  <ActionIcon
                    variant="light"
                    color="red"
                    onClick={() => handleUnmount(mount.mount_point)}
                  >
                    <IconTrash size="1rem" />
                  </ActionIcon>
                </Group>
              </Group>
            </Card>
          ))
        )}
      </Stack>

      {/* Create Mount Modal */}
      <Modal
        opened={createMountModal}
        onClose={() => setCreateMountModal(false)}
        title="Create New Mount"
      >
        <Stack>
          <Select
            label="Remote"
            placeholder="Select a remote to mount"
            data={remotes}
            value={selectedRemote}
            onChange={(value) => setSelectedRemote(value || '')}
          />

          <TextInput
            label="Mount Point"
            value={mountPoint}
            onChange={(event) => setMountPoint(event.currentTarget.value)}
            placeholder="Enter mount point path (e.g., /mnt/rclone)"
          />

          <Group position="right">
            <Button variant="light" onClick={() => setCreateMountModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateMount}>
              Create Mount
            </Button>
          </Group>
        </Stack>
      </Modal>
    </Container>
  )
}

export default Mounts
