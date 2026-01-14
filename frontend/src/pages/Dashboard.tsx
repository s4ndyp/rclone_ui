import { useEffect, useState } from 'react'
import {
  Container,
  Title,
  Grid,
  Card,
  Text,
  Badge,
  Loader,
  Alert,
  Group,
  Stack
} from '@mantine/core'
import { IconServer, IconFolder, IconMount, IconCheck, IconX } from '@tabler/icons-react'
import { apiService } from '../services/api'
import { HealthResponse, MountInfo, JobInfo } from '../types/api'

function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [mounts, setMounts] = useState<MountInfo[]>([])
  const [jobs, setJobs] = useState<JobInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const [healthData, mountsData, jobsData] = await Promise.all([
          apiService.healthCheck(),
          apiService.listMounts(),
          apiService.listJobs(),
        ])

        setHealth(healthData)
        setMounts(mountsData)
        setJobs(jobsData)
      } catch (err) {
        setError('Failed to load dashboard data')
        console.error('Dashboard error:', err)
      } finally {
        setLoading(false)
      }
    }

    loadDashboardData()
  }, [])

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
      <Title order={2} mb="xl">Dashboard</Title>

      <Grid>
        {/* Rclone Status */}
        <Grid.Col span={6}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group position="apart" mb="xs">
              <Text weight={500}>Rclone Status</Text>
              <IconServer size="1.5rem" />
            </Group>

            <Group spacing="xs">
              <Text size="sm" color="dimmed">Connection:</Text>
              <Badge
                color={health?.rclone_connected ? 'green' : 'red'}
                leftSection={health?.rclone_connected ? <IconCheck size="0.8rem" /> : <IconX size="0.8rem" />}
              >
                {health?.rclone_connected ? 'Connected' : 'Disconnected'}
              </Badge>
            </Group>
          </Card>
        </Grid.Col>

        {/* Active Mounts */}
        <Grid.Col span={6}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group position="apart" mb="xs">
              <Text weight={500}>Active Mounts</Text>
              <IconMount size="1.5rem" />
            </Group>

            <Stack spacing="xs">
              <Text size="sm" color="dimmed">Total mounts: {mounts.length}</Text>
              {mounts.length > 0 ? (
                mounts.slice(0, 3).map((mount, index) => (
                  <Text key={index} size="sm" truncate>
                    {mount.mount_point}
                  </Text>
                ))
              ) : (
                <Text size="sm" color="dimmed">No active mounts</Text>
              )}
              {mounts.length > 3 && (
                <Text size="sm" color="dimmed">...and {mounts.length - 3} more</Text>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* Running Jobs */}
        <Grid.Col span={6}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Group position="apart" mb="xs">
              <Text weight={500}>Running Jobs</Text>
              <IconFolder size="1.5rem" />
            </Group>

            <Stack spacing="xs">
              <Text size="sm" color="dimmed">Active jobs: {jobs.length}</Text>
              {jobs.length > 0 ? (
                jobs.slice(0, 3).map((job) => (
                  <Text key={job.id} size="sm">
                    Job #{job.id}
                  </Text>
                ))
              ) : (
                <Text size="sm" color="dimmed">No running jobs</Text>
              )}
              {jobs.length > 3 && (
                <Text size="sm" color="dimmed">...and {jobs.length - 3} more</Text>
              )}
            </Stack>
          </Card>
        </Grid.Col>

        {/* Quick Stats */}
        <Grid.Col span={6}>
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text weight={500} mb="xs">Quick Stats</Text>

            <Stack spacing="xs">
              <Group position="apart">
                <Text size="sm" color="dimmed">Status:</Text>
                <Text size="sm" weight={500}>
                  {health?.status === 'ok' ? 'Operational' : 'Issues detected'}
                </Text>
              </Group>
              <Group position="apart">
                <Text size="sm" color="dimmed">API Version:</Text>
                <Text size="sm" weight={500}>1.0.0</Text>
              </Group>
            </Stack>
          </Card>
        </Grid.Col>
      </Grid>
    </Container>
  )
}

export default Dashboard
