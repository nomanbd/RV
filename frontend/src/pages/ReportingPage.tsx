import {
  Title, Card, Stack, Group, Button, Text,
  SimpleGrid, RingProgress, Tabs, Loader,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { IconChartBar, IconFileReport, IconActivity } from '@tabler/icons-react';
import { reportingApi } from '../api/reporting';

export default function ReportingPage() {
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => reportingApi.getDashboardStats(),
  });

  const { data: utilization = [], isLoading: utilizationLoading } = useQuery({
    queryKey: ['machine-utilization'],
    queryFn: () => reportingApi.getMachineUtilization(),
  });

  return (
    <Stack>
      <Title order={2}>Reports & Analytics</Title>

      <Tabs defaultValue="dashboard">
        <Tabs.List>
          <Tabs.Tab value="dashboard" leftSection={<IconChartBar size={16} />}>Dashboard</Tabs.Tab>
          <Tabs.Tab value="utilization" leftSection={<IconActivity size={16} />}>Machine Utilization</Tabs.Tab>
          <Tabs.Tab value="reports" leftSection={<IconFileReport size={16} />}>Generate Reports</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="dashboard" pt="md">
          {statsLoading ? (
            <Group justify="center" py="xl"><Loader /></Group>
          ) : stats ? (
            <SimpleGrid cols={{ base: 2, md: 4 }}>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Total Patients</Text>
                <Text size="xl" fw={700}>{stats.total_patients}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Active Plans</Text>
                <Text size="xl" fw={700}>{stats.active_plans}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Today's Appointments</Text>
                <Text size="xl" fw={700}>{stats.todays_appointments}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Pending Tasks</Text>
                <Text size="xl" fw={700}>{stats.pending_tasks}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Machines Active</Text>
                <Text size="xl" fw={700}>{stats.machines_active} / {stats.machines_total}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>QA Due</Text>
                <Text size="xl" fw={700} c={stats.qa_due > 0 ? 'orange' : undefined}>{stats.qa_due}</Text>
              </Card>
            </SimpleGrid>
          ) : (
            <Text c="dimmed" ta="center">No data available</Text>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="utilization" pt="md">
          {utilizationLoading ? (
            <Group justify="center" py="xl"><Loader /></Group>
          ) : (
            <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }}>
              {utilization.map((machine) => (
                <Card key={machine.machine_id} withBorder p="lg">
                  <Group justify="space-between" mb="md">
                    <div>
                      <Text fw={700}>{machine.machine_name}</Text>
                      <Text size="sm" c="dimmed">
                        {machine.completed_sessions} / {machine.total_sessions} sessions
                      </Text>
                    </div>
                    <RingProgress
                      size={80}
                      thickness={8}
                      roundCaps
                      sections={[{ value: machine.utilization_percentage, color: machine.utilization_percentage > 80 ? 'green' : 'blue' }]}
                      label={<Text ta="center" size="xs" fw={700}>{machine.utilization_percentage.toFixed(0)}%</Text>}
                    />
                  </Group>
                  <Text size="sm">Total beam-on time: {machine.total_beam_on_minutes.toFixed(0)} min</Text>
                </Card>
              ))}
              {utilization.length === 0 && (
                <Card withBorder p="xl">
                  <Text ta="center" c="dimmed">No utilization data available</Text>
                </Card>
              )}
            </SimpleGrid>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="reports" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Treatment Summary Report</Text>
                <Text size="sm" c="dimmed">Complete treatment summary including prescriptions, plans, fractions delivered, and cumulative dose.</Text>
                <Button variant="light">Generate PDF</Button>
              </Stack>
            </Card>
            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Dose Tracking Report</Text>
                <Text size="sm" c="dimmed">Fraction-by-fraction dose delivery tracking with planned vs. delivered comparison.</Text>
                <Button variant="light">Generate PDF</Button>
              </Stack>
            </Card>
            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Machine QA Report</Text>
                <Text size="sm" c="dimmed">Summary of QA checks, pass/fail rates, and compliance metrics for each machine.</Text>
                <Button variant="light">Generate PDF</Button>
              </Stack>
            </Card>
            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Compliance Report</Text>
                <Text size="sm" c="dimmed">21 CFR Part 11 compliance summary including electronic signatures and audit trail statistics.</Text>
                <Button variant="light">Generate PDF</Button>
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
