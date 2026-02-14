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
} from '@mantine/core';
import {
  RiUserLine,
  RiPulseLine,
  RiCalendarLine,
  RiShieldCheckLine,
  RiHospitalLine,
  RiFileList3Line,
} from 'react-icons/ri';
import { useAppStore } from '../store';

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
          <Text size="xs" c="dimmed" tt="uppercase" fw={700}>
            {title}
          </Text>
          <Text fw={700} size="xl">
            {value}
          </Text>
          {description && (
            <Text size="xs" c="dimmed">{description}</Text>
          )}
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

  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Title order={2}>Dashboard</Title>
          <Text c="dimmed">
            Welcome back, {user?.title ? `${user.title} ` : ''}{user?.first_name}
          </Text>
        </div>
        <Badge color="green" size="lg" variant="light">System Online</Badge>
      </Group>

      <SimpleGrid cols={{ base: 1, sm: 2, lg: 3 }}>
        <StatCard
          title="Active Patients"
          value="--"
          icon={RiUserLine}
          color="blue"
          description="Total active patients"
        />
        <StatCard
          title="Today's Treatments"
          value="--"
          icon={RiPulseLine}
          color="green"
          description="Scheduled for today"
        />
        <StatCard
          title="Appointments"
          value="--"
          icon={RiCalendarLine}
          color="orange"
          description="This week"
        />
        <StatCard
          title="Plans Pending Review"
          value="--"
          icon={RiFileList3Line}
          color="yellow"
          description="Awaiting approval"
        />
        <StatCard
          title="Machines Online"
          value="--"
          icon={RiHospitalLine}
          color="teal"
          description="Active treatment units"
        />
        <StatCard
          title="QA Tasks"
          value="--"
          icon={RiShieldCheckLine}
          color="violet"
          description="Pending completion"
        />
      </SimpleGrid>

      <Grid>
        <Grid.Col span={{ base: 12, md: 8 }}>
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="md">Today's Treatment Schedule</Title>
            <Text c="dimmed" ta="center" py="xl">
              Treatment schedule will appear here once data is loaded.
            </Text>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 4 }}>
          <Card withBorder p="md" radius="md">
            <Title order={4} mb="md">Notifications</Title>
            <Text c="dimmed" ta="center" py="xl">
              No new notifications.
            </Text>
          </Card>
        </Grid.Col>
      </Grid>
    </Stack>
  );
}
