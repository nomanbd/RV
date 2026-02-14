import { Title, Card, Text, Stack } from '@mantine/core';

export default function MachineManagementPage() {
  return (
    <Stack>
      <Title order={2}>Treatment Machines</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          Manage treatment machines, tolerance tables, and QA schedules.
          Configure DICOM AE titles and machine capabilities.
        </Text>
      </Card>
    </Stack>
  );
}
