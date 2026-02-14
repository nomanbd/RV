import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppShell,
  Burger,
  Group,
  NavLink,
  Title,
  Text,
  Avatar,
  Menu,
  UnstyledButton,
  Divider,
  Badge,
} from '@mantine/core';
import {
  RiDashboardLine,
  RiUserLine,
  RiFileList3Line,
  RiPulseLine,
  RiImage2Line,
  RiCalendarLine,
  RiBarChartLine,
  RiSettings3Line,
  RiShieldCheckLine,
  RiLogoutBoxLine,
  RiAdminLine,
  RiHospitalLine,
} from 'react-icons/ri';
import { useAppStore } from '../../store';
import PatientBanner from './PatientBanner';

const navItems = [
  { label: 'Dashboard', icon: RiDashboardLine, path: '/' },
  { label: 'Patients', icon: RiUserLine, path: '/patients' },
  { label: 'Treatment Plans', icon: RiFileList3Line, path: '/plans' },
  { label: 'Treatment Console', icon: RiPulseLine, path: '/treatment' },
  { label: 'Imaging', icon: RiImage2Line, path: '/imaging' },
  { label: 'Scheduling', icon: RiCalendarLine, path: '/scheduling' },
  { label: 'Reports', icon: RiBarChartLine, path: '/reports' },
  { label: 'divider', icon: RiDashboardLine, path: '' },
  { label: 'Machines', icon: RiHospitalLine, path: '/admin/machines' },
  { label: 'QA', icon: RiShieldCheckLine, path: '/admin/qa' },
  { label: 'Users', icon: RiAdminLine, path: '/admin/users' },
  { label: 'Audit Log', icon: RiShieldCheckLine, path: '/admin/audit' },
  { label: 'Settings', icon: RiSettings3Line, path: '/admin/settings' },
];

export default function Layout() {
  const [opened, setOpened] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, clearAuth, selectedPatient } = useAppStore();

  const handleLogout = () => {
    clearAuth();
    navigate('/login');
  };

  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 250, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={opened} onClick={() => setOpened((o) => !o)} hiddenFrom="sm" size="sm" />
            <RiPulseLine size={28} color="var(--mantine-color-blue-6)" />
            <Title order={3} c="blue.7">RadOnc R&V</Title>
            <Badge variant="light" color="green" size="sm">v0.1</Badge>
          </Group>

          <Group>
            {selectedPatient && (
              <PatientBanner patient={selectedPatient} compact />
            )}
            <Menu shadow="md" width={200}>
              <Menu.Target>
                <UnstyledButton>
                  <Group gap="xs">
                    <Avatar radius="xl" size="sm" color="blue">
                      {user?.first_name?.[0]}{user?.last_name?.[0]}
                    </Avatar>
                    <div style={{ lineHeight: 1 }}>
                      <Text size="sm" fw={500}>{user?.first_name} {user?.last_name}</Text>
                      <Text size="xs" c="dimmed">{user?.roles?.[0]?.name?.replace('_', ' ')}</Text>
                    </div>
                  </Group>
                </UnstyledButton>
              </Menu.Target>
              <Menu.Dropdown>
                <Menu.Label>Account</Menu.Label>
                <Menu.Item onClick={() => navigate('/admin/settings')}>
                  Settings
                </Menu.Item>
                <Menu.Divider />
                <Menu.Item color="red" leftSection={<RiLogoutBoxLine />} onClick={handleLogout}>
                  Logout
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Navbar p="xs">
        {navItems.map((item) =>
          item.label === 'divider' ? (
            <Divider my="xs" key="divider" label="Administration" labelPosition="center" />
          ) : (
            <NavLink
              key={item.path}
              label={item.label}
              leftSection={<item.icon size={18} />}
              active={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setOpened(false);
              }}
              variant="light"
            />
          )
        )}
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
