import { Title, Card, Text, Stack } from '@mantine/core';

export default function SettingsPage() {
  return (
    <Stack>
      <Title order={2}>Settings</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          System configuration: DICOM peer management, global settings,
          tolerance defaults, and integration configuration.
        </Text>
      </Card>
    </Stack>
  );
}
