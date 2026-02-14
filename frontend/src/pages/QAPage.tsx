import { Title, Card, Text, Stack } from '@mantine/core';

export default function QAPage() {
  return (
    <Stack>
      <Title order={2}>Quality Assurance</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          Manage QA checklists, submit QA records, and track compliance.
          Supports daily/weekly/monthly machine QA and patient-specific QA.
        </Text>
      </Card>
    </Stack>
  );
}
