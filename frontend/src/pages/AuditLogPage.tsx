import { Title, Card, Text, Stack } from '@mantine/core';

export default function AuditLogPage() {
  return (
    <Stack>
      <Title order={2}>Audit Log</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          21 CFR Part 11 compliant audit trail. All data creation, modification,
          and deletion events are permanently recorded with timestamps,
          user identification, and change details.
        </Text>
      </Card>
    </Stack>
  );
}
