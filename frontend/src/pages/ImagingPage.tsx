import { Title, Card, Text, Stack } from '@mantine/core';

export default function ImagingPage() {
  return (
    <Stack>
      <Title order={2}>Image Guidance</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          DICOM image viewer with Cornerstone3D integration.
          Import portal images, CBCT, kV/kV, and DRR images for position verification.
        </Text>
      </Card>
    </Stack>
  );
}
