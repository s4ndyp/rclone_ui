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
  Badge,
  Button,
} from '@mantine/core'
import { IconSettings, IconX } from '@tabler/icons-react'
import { apiService } from '../services/api'

function Remotes() {
  const [config, setConfig] = useState<Record<string, any>>({})
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const configData = await apiService.getConfig()
      setConfig(configData)
    } catch (err) {
      setError('Failed to load configuration')
      console.error('Load config error:', err)
    } finally {
      setLoading(false)
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

  const remoteNames = Object.keys(config)

  return (
    <Container size="xl">
      <Group position="apart" mb="xl">
        <Title order={2}>Remotes</Title>
        <Button leftIcon={<IconSettings size="1rem" />}>
          Add Remote
        </Button>
      </Group>

      <Stack spacing="md">
        {remoteNames.length === 0 ? (
          <Card shadow="sm" padding="lg" radius="md" withBorder>
            <Text align="center" color="dimmed">
              No remotes configured yet. Click "Add Remote" to get started.
            </Text>
          </Card>
        ) : (
          remoteNames.map((remoteName) => (
            <Card key={remoteName} shadow="sm" padding="lg" radius="md" withBorder>
              <Group position="apart" mb="xs">
                <Text weight={500} size="lg">{remoteName}</Text>
                <Badge color="blue" size="sm">
                  {config[remoteName].type || 'Unknown'}
                </Badge>
              </Group>

              <Stack spacing="xs">
                <Text size="sm" color="dimmed">
                  Type: {config[remoteName].type || 'Unknown'}
                </Text>
                {config[remoteName].path && (
                  <Text size="sm" color="dimmed">
                    Path: {config[remoteName].path}
                  </Text>
                )}
                {config[remoteName].region && (
                  <Text size="sm" color="dimmed">
                    Region: {config[remoteName].region}
                  </Text>
                )}
              </Stack>
            </Card>
          ))
        )}
      </Stack>
    </Container>
  )
}

export default Remotes
