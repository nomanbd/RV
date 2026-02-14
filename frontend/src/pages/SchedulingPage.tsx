import { Title, Card, Text, Stack } from '@mantine/core';

export default function SchedulingPage() {
  return (
    <Stack>
      <Title order={2}>Scheduling</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          Appointment scheduling calendar with machine resource views.
          Manage treatment, simulation, and consultation appointments.
        </Text>
      </Card>
    </Stack>
  );
}
