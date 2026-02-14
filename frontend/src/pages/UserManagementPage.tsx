import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text, Modal,
  TextInput, MultiSelect, Loader, ActionIcon, Tooltip,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconEdit } from '@tabler/icons-react';
import api from '../api/client';
import type { User } from '../types/auth';

const STATUS_COLORS: Record<string, string> = {
  active: 'green',
  inactive: 'gray',
  locked: 'red',
};

const ROLES = [
  { value: 'admin', label: 'Administrator' },
  { value: 'radiation_oncologist', label: 'Radiation Oncologist' },
  { value: 'physicist', label: 'Medical Physicist' },
  { value: 'therapist', label: 'Radiation Therapist' },
  { value: 'dosimetrist', label: 'Dosimetrist' },
  { value: 'nurse', label: 'Nurse' },
];

export default function UserManagementPage() {
  const queryClient = useQueryClient();
  const [createModalOpen, setCreateModalOpen] = useState(false);

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => api.get<User[]>('/users').then(r => r.data),
  });

  const createForm = useForm({
    initialValues: {
      username: '',
      email: '',
      password: '',
      first_name: '',
      last_name: '',
      title: '',
      professional_id: '',
      roles: [] as string[],
    },
  });

  const createUserMutation = useMutation({
    mutationFn: (data: typeof createForm.values) => api.post('/users', data).then(r => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setCreateModalOpen(false);
      createForm.reset();
      notifications.show({ title: 'Success', message: 'User created', color: 'green' });
    },
    onError: () => {
      notifications.show({ title: 'Error', message: 'Failed to create user', color: 'red' });
    },
  });

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>User Management</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setCreateModalOpen(true)}>Add User</Button>
      </Group>

      <Card withBorder>
        {isLoading ? (
          <Group justify="center" py="xl"><Loader /></Group>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Username</Table.Th>
                <Table.Th>Name</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Title</Table.Th>
                <Table.Th>Roles</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {users.map((user) => (
                <Table.Tr key={user.id}>
                  <Table.Td><Text fw={600}>{user.username}</Text></Table.Td>
                  <Table.Td>{user.first_name} {user.last_name}</Table.Td>
                  <Table.Td>{user.email}</Table.Td>
                  <Table.Td>{user.title || '-'}</Table.Td>
                  <Table.Td>
                    <Group gap={4}>
                      {user.roles?.map((role) => (
                        <Badge key={role.id} size="sm" variant="outline">{role.name.replace(/_/g, ' ')}</Badge>
                      )) || '-'}
                    </Group>
                  </Table.Td>
                  <Table.Td>
                    <Badge color={STATUS_COLORS[user.status] || 'gray'}>{user.status}</Badge>
                  </Table.Td>
                  <Table.Td>
                    <Tooltip label="Edit">
                      <ActionIcon variant="subtle"><IconEdit size={16} /></ActionIcon>
                    </Tooltip>
                  </Table.Td>
                </Table.Tr>
              ))}
              {users.length === 0 && (
                <Table.Tr>
                  <Table.Td colSpan={7}>
                    <Text ta="center" c="dimmed" py="xl">No users found</Text>
                  </Table.Td>
                </Table.Tr>
              )}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      <Modal opened={createModalOpen} onClose={() => setCreateModalOpen(false)} title="Create User" size="lg">
        <form onSubmit={createForm.onSubmit((values) => createUserMutation.mutate(values))}>
          <Stack>
            <Group grow>
              <TextInput label="Username" required {...createForm.getInputProps('username')} />
              <TextInput label="Email" required type="email" {...createForm.getInputProps('email')} />
            </Group>
            <TextInput label="Password" required type="password" {...createForm.getInputProps('password')} />
            <Group grow>
              <TextInput label="First Name" required {...createForm.getInputProps('first_name')} />
              <TextInput label="Last Name" required {...createForm.getInputProps('last_name')} />
            </Group>
            <Group grow>
              <TextInput label="Title" placeholder="e.g. MD, PhD, RTT" {...createForm.getInputProps('title')} />
              <TextInput label="Professional ID" {...createForm.getInputProps('professional_id')} />
            </Group>
            <MultiSelect label="Roles" data={ROLES} {...createForm.getInputProps('roles')} />
            <Button type="submit" loading={createUserMutation.isPending}>Create User</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
