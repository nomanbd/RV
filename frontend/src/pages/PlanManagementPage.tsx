import { Title, Card, Text, Stack, Button, Group } from '@mantine/core';
import { RiUploadLine } from 'react-icons/ri';

export default function PlanManagementPage() {
  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Treatment Plans</Title>
        <Button leftSection={<RiUploadLine />}>Import DICOM RT Plan</Button>
      </Group>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          Import DICOM RT Plan files to begin managing treatment plans.
          Supports RT Plan, RT Dose, and RT Structure Set.
        </Text>
      </Card>
    </Stack>
  );
}
