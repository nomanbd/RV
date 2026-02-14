import {
  Title,
  Grid,
  Card,
  Text,
  Group,
  ThemeIcon,
  Stack,
  Badge,
  SimpleGrid,
  Table,
  Loader,
  Center,
  Paper,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  RiUserLine,
  RiPulseLine,
  RiCalendarLine,
  RiShieldCheckLine,
  RiHospitalLine,
  RiFileList3Line,
  RiTimeLine,
} from 'react-icons/ri';
import { useAppStore } from '../store';
import { reportingApi } from '../api/reporting';
import { schedulingApi } from '../api/scheduling';
import { planningApi } from '../api/planning';

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ComponentType<{ size: number }>;
  color: string;
  description?: string;
}

function StatCard({ title, value, icon: Icon, color, description }: StatCardProps) {
  return (
    <Card withBorder p="md" radius="md">
      <Group justify="space-between">
        <div>
          <Text size="xs" c="dimmed" tt="uppercase" fw={700}>{title}</Text>
          <Text fw={700} size="xl">{value}</Text>
          {description && <Text size="xs" c="dimmed">{description}</Text>}
        </div>
        <ThemeIcon color={color} variant="light" size={48} radius="md">
          <Icon size={28} />
        </ThemeIcon>
      </Group>
    </Card>
  );
}

export default function DashboardPage() {
  const { user } = useAppStore();

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => reportingApi.getDashboardStats(),
    retry: false,
  });

  const today = new Date().toISOString().split('T')[0];
  const { data: todayAppts = [] } = useQuery({
    queryKey: ['today-appointments', today],
    queryFn: () => schedulingApi.listAppointments({ date_from: today, date_to: today, limit: 10 }),
    retry: false,
  });

  const { data: notifs = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => schedulingApi.getNotifications(true),
    retry: false,
  });

  const { data: pendingPlans = [] } = useQuery({
    queryKey: ['pending-plans'],
    queryFn: () => planningApi.listPlans({ status: 'pending_review', limit: 5 }),
    retry: false,
  });

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed">Welcome back, {user?.title ? `${user.title} ` : ''}{user?.first_name}</Text>
        </div>
        <Badge color="green" size="lg" variant="light">System Online</Badge>
      </Group>

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        {statsLoading ? (
          <Card withBorder p="md"><Center py="md"><Loader size="sm" /></Center></Card>
        ) : (
          <>
            <StatCard title="Active Patients" value={stats?.total_patients?.toString() || '0'} icon={RiUserLine} color="blue" description="Total active patients" />
            <StatCard title="Today's Treatments" value={stats?.todays_appointments?.toString() || '0'} icon={RiPulseLine} color="green" description="Scheduled for today" />
            <StatCard title="Appointments" value={todayAppts.length.toString()} icon={RiCalendarLine} color="orange" description="Today's schedule" />
            <StatCard title="Plans Pending Review" value={stats?.active_plans?.toString() || '0'} icon={RiFileList3Line} color="yellow" description="Awaiting approval" />
            <StatCard title="Machines Online" value={stats ? `${stats.machines_active}/${stats.machines_total}` : '0'} icon={RiHospitalLine} color="teal" description="Active treatment units" />
            <StatCard title="QA Tasks" value={stats?.qa_due?.toString() || '0'} icon={RiShieldCheckLine} color="violet" description="Pending completion" />
          </>
        )}
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="md">Today's Treatment Schedule</Title>
            {todayAppts.length > 0 ? (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Time</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Patient</Table.Th>
                    <Table.Th>Status</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {todayAppts.map((appt) => (
                    <Table.Tr key={appt.id}>
                      <Table.Td>
                        <Text size="sm" fw={500}>
                          {new Date(appt.scheduled_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </Text>
                      </Table.Td>
                      <Table.Td><Badge size="sm" variant="light">{appt.appointment_type}</Badge></Table.Td>
                      <Table.Td><Text size="sm">{appt.patient_id}</Text></Table.Td>
                      <Table.Td>
                        <Badge size="sm" color={appt.status === 'completed' ? 'green' : appt.status === 'in_progress' ? 'blue' : 'gray'}>
                          {appt.status}
                        </Badge>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            ) : (
              <Text c="dimmed" ta="center" py="xl">No appointments scheduled for today.</Text>
            )}
          </Card>

          {pendingPlans.length > 0 && (
            <Card withBorder p="md" radius="md" mt="md">
              <Title order={4} mb="md">Plans Awaiting Review</Title>
              <Stack gap="xs">
                {pendingPlans.map((plan) => (
                  <Paper key={plan.id} withBorder p="sm" radius="sm">
                    <Group justify="space-between">
                      <div>
                        <Text size="sm" fw={600}>{plan.plan_label}</Text>
                        <Text size="xs" c="dimmed">{plan.num_beams} beams | v{plan.version} | {new Date(plan.created_at).toLocaleDateString()}</Text>
                      </div>
                      <Badge color="yellow" variant="light">Pending Review</Badge>
                    </Group>
                  </Paper>
                ))}
              </Stack>
            </Card>
          )}
        </Grid.Col>

        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="md">Notifications</Title>
            {notifs.length > 0 ? (
              <Stack gap="xs">
                {notifs.slice(0, 5).map((notif) => (
                  <Paper key={notif.id} withBorder p="sm" radius="sm">
                    <Group gap="xs" mb={4}>
                      <ThemeIcon size="xs" color="blue" variant="light" radius="xl"><RiTimeLine size={10} /></ThemeIcon>
                      <Text size="xs" c="dimmed">{new Date(notif.created_at).toLocaleString()}</Text>
                    </Group>
                    <Text size="sm">{notif.message}</Text>
                  </Paper>
                ))}
              </Stack>
            ) : (
              <Text c="dimmed" ta="center" py="xl">No new notifications.</Text>
            )}
          </Card>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
