import { Routes, Route } from 'react-router-dom'
import { AppShell, Navbar, Header, Title, NavLink, Group } from '@mantine/core'
import { IconFolder, IconSettings, IconServer, IconMount } from '@tabler/icons-react'
import Dashboard from './pages/Dashboard'
import FileExplorer from './pages/FileExplorer'
import Remotes from './pages/Remotes'
import Mounts from './pages/Mounts'
import { Link, useLocation } from 'react-router-dom'

function App() {
  const location = useLocation()

  const navigationItems = [
    { label: 'Dashboard', path: '/', icon: IconServer },
    { label: 'File Explorer', path: '/files', icon: IconFolder },
    { label: 'Remotes', path: '/remotes', icon: IconSettings },
    { label: 'Mounts', path: '/mounts', icon: IconMount },
  ]

  return (
    <AppShell
      padding="md"
      navbar={
        <Navbar width={{ base: 300 }} p="xs">
          <Navbar.Section grow>
            {navigationItems.map((item) => (
              <NavLink
                key={item.path}
                label={item.label}
                icon={<item.icon size="1rem" stroke={1.5} />}
                component={Link}
                to={item.path}
                active={location.pathname === item.path}
              />
            ))}
          </Navbar.Section>
        </Navbar>
      }
      header={
        <Header height={60} p="xs">
          <Group position="apart" px="md">
            <Title order={3}>Rclone Web GUI</Title>
          </Group>
        </Header>
      }
      styles={(theme) => ({
        main: {
          backgroundColor:
            theme.colorScheme === 'dark'
              ? theme.colors.dark[8]
              : theme.colors.gray[0],
        },
      })}
    >
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/files" element={<FileExplorer />} />
        <Route path="/remotes" element={<Remotes />} />
        <Route path="/mounts" element={<Mounts />} />
      </Routes>
    </AppShell>
  )
}

export default App
