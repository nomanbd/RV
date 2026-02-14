import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text, Modal,
  TextInput, Select, Switch, Tabs, ActionIcon, Tooltip, Loader,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconEdit, IconSettings } from '@tabler/icons-react';
import { machinesApi } from '../api/machines';

const STATUS_COLORS: Record<string, string> = {
  active: 'green',
  maintenance: 'yellow',
  decommissioned: 'red',
};

export default function MachineManagementPage() {
  const queryClient = useQueryClient();
  const [machineModalOpen, setMachineModalOpen] = useState(false);
  const { data: machines = [], isLoading } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machinesApi.listMachines(),
  });

  const machineForm = useForm({
    initialValues: {
      name: '',
      machine_type: 'linac',
      manufacturer: '',
      model: '',
      serial_number: '',
      dicom_ae_title: '',
      location: '',
      has_mlc: true,
      has_epid: true,
      has_cbct: false,
      has_kv_imaging: false,
    },
  });

  const createMachineMutation = useMutation({
    mutationFn: (data: typeof machineForm.values) => machinesApi.createMachine(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setMachineModalOpen(false);
      machineForm.reset();
      notifications.show({ title: 'Success', message: 'Machine created', color: 'green' });
    },
  });

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Machine Management</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setMachineModalOpen(true)}>
          Add Machine
        </Button>
      </Group>

      <Tabs defaultValue="machines">
        <Tabs.List>
          <Tabs.Tab value="machines">Treatment Machines</Tabs.Tab>
          <Tabs.Tab value="tolerances">Tolerance Tables</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="machines" pt="md">
          <Card withBorder>
            {isLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Manufacturer</Table.Th>
                    <Table.Th>Model</Table.Th>
                    <Table.Th>AE Title</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Capabilities</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {machines.map((machine) => (
                    <Table.Tr key={machine.id}>
                      <Table.Td>
                        <Text fw={600}>{machine.name}</Text>
                        {machine.location && <Text size="xs" c="dimmed">{machine.location}</Text>}
                      </Table.Td>
                      <Table.Td>{machine.machine_type}</Table.Td>
                      <Table.Td>{machine.manufacturer || '-'}</Table.Td>
                      <Table.Td>{machine.model || '-'}</Table.Td>
                      <Table.Td><Text size="sm" style={{ fontFamily: 'monospace' }}>{machine.dicom_ae_title || '-'}</Text></Table.Td>
                      <Table.Td>
                        <Badge color={STATUS_COLORS[machine.status] || 'gray'}>{machine.status}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Group gap={4}>
                          {machine.has_mlc && <Badge size="xs" variant="outline">MLC</Badge>}
                          {machine.has_epid && <Badge size="xs" variant="outline">EPID</Badge>}
                          {machine.has_cbct && <Badge size="xs" variant="outline">CBCT</Badge>}
                          {machine.has_kv_imaging && <Badge size="xs" variant="outline">kV</Badge>}
                        </Group>
                      </Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="Edit">
                            <ActionIcon variant="subtle" onClick={() => { /* TODO: edit machine */ }}>
                              <IconEdit size={16} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="Tolerances">
                            <ActionIcon variant="subtle" color="blue">
                              <IconSettings size={16} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {machines.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={8}>
                        <Text ta="center" c="dimmed" py="xl">No machines configured</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="tolerances" pt="md">
          <Card withBorder p="xl">
            <Stack align="center">
              <Text c="dimmed">
                Tolerance tables define acceptable parameter deviations for beam verification.
                Each machine can have multiple tolerance tables for different treatment techniques.
              </Text>
              <Button leftSection={<IconPlus size={16} />} variant="light">
                Create Tolerance Table
              </Button>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Create Machine Modal */}
      <Modal opened={machineModalOpen} onClose={() => setMachineModalOpen(false)} title="Add Treatment Machine" size="lg">
        <form onSubmit={machineForm.onSubmit((values) => createMachineMutation.mutate(values))}>
          <Stack>
            <TextInput label="Machine Name" required {...machineForm.getInputProps('name')} />
            <Select
              label="Machine Type"
              data={[
                { value: 'linac', label: 'Linear Accelerator' },
                { value: 'cobalt', label: 'Cobalt-60' },
                { value: 'cyberknife', label: 'CyberKnife' },
                { value: 'tomotherapy', label: 'TomoTherapy' },
                { value: 'proton', label: 'Proton Therapy' },
              ]}
              {...machineForm.getInputProps('machine_type')}
            />
            <Group grow>
              <TextInput label="Manufacturer" {...machineForm.getInputProps('manufacturer')} />
              <TextInput label="Model" {...machineForm.getInputProps('model')} />
            </Group>
            <Group grow>
              <TextInput label="Serial Number" {...machineForm.getInputProps('serial_number')} />
              <TextInput label="DICOM AE Title" {...machineForm.getInputProps('dicom_ae_title')} />
            </Group>
            <TextInput label="Location" {...machineForm.getInputProps('location')} />
            <Group>
              <Switch label="MLC" {...machineForm.getInputProps('has_mlc', { type: 'checkbox' })} />
              <Switch label="EPID" {...machineForm.getInputProps('has_epid', { type: 'checkbox' })} />
              <Switch label="CBCT" {...machineForm.getInputProps('has_cbct', { type: 'checkbox' })} />
              <Switch label="kV Imaging" {...machineForm.getInputProps('has_kv_imaging', { type: 'checkbox' })} />
            </Group>
            <Button type="submit" loading={createMachineMutation.isPending}>Create Machine</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
