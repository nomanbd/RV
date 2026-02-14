import { Title, Card, Text, Stack } from '@mantine/core';

export default function UserManagementPage() {
  return (
    <Stack>
      <Title order={2}>User Management</Title>
      <Card withBorder p="xl">
        <Text c="dimmed" ta="center" py="xl">
          Manage users, roles, and permissions. Assign staff roles
          (Radiation Oncologist, Physicist, Therapist, Dosimetrist, Nurse).
        </Text>
      </Card>
    </Stack>
  );
}
