import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text, Modal,
  TextInput, Select, Switch, Tabs, ActionIcon, Tooltip, Loader,
  NumberInput, Grid,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconEdit, IconSettings } from '@tabler/icons-react';
import { machinesApi } from '../api/machines';
import type { TreatmentMachine } from '../types/machine';

const STATUS_COLORS: Record<string, string> = {
  active: 'green', maintenance: 'yellow', decommissioned: 'red',
};

export default function MachineManagementPage() {
  const queryClient = useQueryClient();
  const [machineModalOpen, setMachineModalOpen] = useState(false);
  const [toleranceModalOpen, setToleranceModalOpen] = useState(false);
  const [editingMachine, setEditingMachine] = useState<TreatmentMachine | null>(null);
  const [selectedMachineForTol, setSelectedMachineForTol] = useState<string | null>(null);

  const { data: machines = [], isLoading } = useQuery({
    queryKey: ['machines'],
    queryFn: () => machinesApi.listMachines(),
  });

  const { data: tolerances = [], isLoading: tolLoading } = useQuery({
    queryKey: ['tolerances', selectedMachineForTol],
    queryFn: () => selectedMachineForTol ? machinesApi.listMachineTolerances(selectedMachineForTol) : Promise.resolve([]),
    enabled: !!selectedMachineForTol,
  });

  const machineForm = useForm({
    initialValues: {
      name: '', machine_type: 'linac', manufacturer: '', model: '',
      serial_number: '', dicom_ae_title: '', location: '',
      has_mlc: true, has_epid: true, has_cbct: false, has_kv_imaging: false,
    },
  });

  const toleranceForm = useForm({
    initialValues: {
      name: '', description: '', machine_id: '' as string | null,
      gantry_angle_tol: 1.0, collimator_angle_tol: 1.0, couch_angle_tol: 1.0,
      couch_vertical_tol: 2.0, couch_lateral_tol: 2.0, couch_longitudinal_tol: 2.0,
      jaw_x_tol: 2.0, jaw_y_tol: 2.0, mlc_tol: 2.0,
      mu_tol: 1.0, dose_rate_tol: 20.0, energy_tol: 0.0,
    },
  });

  const createMachineMut = useMutation({
    mutationFn: (data: typeof machineForm.values) => machinesApi.createMachine(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setMachineModalOpen(false);
      machineForm.reset();
      notifications.show({ title: 'Success', message: 'Machine created', color: 'green' });
    },
  });

  const updateMachineMut = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<TreatmentMachine> }) => machinesApi.updateMachine(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['machines'] });
      setEditingMachine(null);
      setMachineModalOpen(false);
      machineForm.reset();
      notifications.show({ title: 'Success', message: 'Machine updated', color: 'green' });
    },
  });

  const createToleranceMut = useMutation({
    mutationFn: (data: typeof toleranceForm.values) => machinesApi.createTolerance(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tolerances'] });
      setToleranceModalOpen(false);
      toleranceForm.reset();
      notifications.show({ title: 'Success', message: 'Tolerance table created', color: 'green' });
    },
  });

  const handleEditMachine = (machine: TreatmentMachine) => {
    setEditingMachine(machine);
    machineForm.setValues({
      name: machine.name,
      machine_type: machine.machine_type,
      manufacturer: machine.manufacturer || '',
      model: machine.model || '',
      serial_number: machine.serial_number || '',
      dicom_ae_title: machine.dicom_ae_title || '',
      location: machine.location || '',
      has_mlc: machine.has_mlc,
      has_epid: machine.has_epid,
      has_cbct: machine.has_cbct,
      has_kv_imaging: machine.has_kv_imaging,
    });
    setMachineModalOpen(true);
  };

  const handleOpenToleranceForMachine = (machineId: string) => {
    setSelectedMachineForTol(machineId);
    toleranceForm.setFieldValue('machine_id', machineId);
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Machine Management</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => { setEditingMachine(null); machineForm.reset(); setMachineModalOpen(true); }}>
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
                      <Table.Td><Badge color={STATUS_COLORS[machine.status] || 'gray'}>{machine.status}</Badge></Table.Td>
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
                            <ActionIcon variant="subtle" onClick={() => handleEditMachine(machine)}>
                              <IconEdit size={16} />
                            </ActionIcon>
                          </Tooltip>
                          <Tooltip label="Tolerances">
                            <ActionIcon variant="subtle" color="blue" onClick={() => handleOpenToleranceForMachine(machine.id)}>
                              <IconSettings size={16} />
                            </ActionIcon>
                          </Tooltip>
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {machines.length === 0 && (
                    <Table.Tr><Table.Td colSpan={8}><Text ta="center" c="dimmed" py="xl">No machines configured</Text></Table.Td></Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="tolerances" pt="md">
          <Stack>
            <Group justify="space-between">
              <Select
                placeholder="Select machine to view tolerances"
                data={machines.map((m) => ({ value: m.id, label: m.name }))}
                value={selectedMachineForTol}
                onChange={setSelectedMachineForTol}
                w={300}
              />
              <Button leftSection={<IconPlus size={16} />} variant="light" onClick={() => { toleranceForm.reset(); if (selectedMachineForTol) toleranceForm.setFieldValue('machine_id', selectedMachineForTol); setToleranceModalOpen(true); }}>
                Create Tolerance Table
              </Button>
            </Group>

            {selectedMachineForTol ? (
              tolLoading ? (
                <Group justify="center" py="xl"><Loader /></Group>
              ) : tolerances.length > 0 ? (
                <Table striped withTableBorder>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Name</Table.Th>
                      <Table.Th>Gantry</Table.Th>
                      <Table.Th>Coll</Table.Th>
                      <Table.Th>Couch</Table.Th>
                      <Table.Th>Jaw X</Table.Th>
                      <Table.Th>Jaw Y</Table.Th>
                      <Table.Th>MLC</Table.Th>
                      <Table.Th>MU</Table.Th>
                      <Table.Th>Dose Rate</Table.Th>
                      <Table.Th>Active</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {tolerances.map((tol) => (
                      <Table.Tr key={tol.id}>
                        <Table.Td>
                          <Text fw={600} size="sm">{tol.name}</Text>
                          {tol.description && <Text size="xs" c="dimmed">{tol.description}</Text>}
                        </Table.Td>
                        <Table.Td>{tol.gantry_angle_tol ?? '-'}°</Table.Td>
                        <Table.Td>{tol.collimator_angle_tol ?? '-'}°</Table.Td>
                        <Table.Td>{tol.couch_angle_tol ?? '-'}°</Table.Td>
                        <Table.Td>{tol.jaw_x_tol ?? '-'} mm</Table.Td>
                        <Table.Td>{tol.jaw_y_tol ?? '-'} mm</Table.Td>
                        <Table.Td>{tol.mlc_tol ?? '-'} mm</Table.Td>
                        <Table.Td>{tol.mu_tol ?? '-'} MU</Table.Td>
                        <Table.Td>{tol.dose_rate_tol ?? '-'}</Table.Td>
                        <Table.Td><Badge color={tol.is_active ? 'green' : 'gray'}>{tol.is_active ? 'Yes' : 'No'}</Badge></Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              ) : (
                <Card withBorder p="xl"><Text ta="center" c="dimmed">No tolerance tables for this machine. Create one to define acceptable parameter deviations.</Text></Card>
              )
            ) : (
              <Card withBorder p="xl"><Text ta="center" c="dimmed">Select a machine above to view or create tolerance tables.</Text></Card>
            )}
          </Stack>
        </Tabs.Panel>
      </Tabs>

      {/* Machine Modal */}
      <Modal opened={machineModalOpen} onClose={() => { setMachineModalOpen(false); setEditingMachine(null); }} title={editingMachine ? 'Edit Treatment Machine' : 'Add Treatment Machine'} size="lg">
        <form onSubmit={machineForm.onSubmit((values) =>
          editingMachine ? updateMachineMut.mutate({ id: editingMachine.id, data: values }) : createMachineMut.mutate(values)
        )}>
          <Stack>
            <TextInput label="Machine Name" required {...machineForm.getInputProps('name')} />
            <Select label="Machine Type" data={[
              { value: 'linac', label: 'Linear Accelerator' },
              { value: 'cobalt', label: 'Cobalt-60' },
              { value: 'cyberknife', label: 'CyberKnife' },
              { value: 'tomotherapy', label: 'TomoTherapy' },
              { value: 'proton', label: 'Proton Therapy' },
            ]} {...machineForm.getInputProps('machine_type')} />
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
            <Button type="submit" loading={editingMachine ? updateMachineMut.isPending : createMachineMut.isPending}>
              {editingMachine ? 'Update Machine' : 'Create Machine'}
            </Button>
          </Stack>
        </form>
      </Modal>

      {/* Tolerance Table Modal */}
      <Modal opened={toleranceModalOpen} onClose={() => setToleranceModalOpen(false)} title="Create Tolerance Table" size="lg">
        <form onSubmit={toleranceForm.onSubmit((values) => createToleranceMut.mutate(values))}>
          <Stack>
            <TextInput label="Name" placeholder="e.g., Standard IMRT Tolerances" required {...toleranceForm.getInputProps('name')} />
            <TextInput label="Description" {...toleranceForm.getInputProps('description')} />
            <Select label="Machine" data={machines.map((m) => ({ value: m.id, label: m.name }))} {...toleranceForm.getInputProps('machine_id')} />
            <Text size="sm" fw={600} mt="xs">Angular Tolerances (degrees)</Text>
            <Grid>
              <Grid.Col span={4}><NumberInput label="Gantry" step={0.1} decimalScale={1} {...toleranceForm.getInputProps('gantry_angle_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="Collimator" step={0.1} decimalScale={1} {...toleranceForm.getInputProps('collimator_angle_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="Couch" step={0.1} decimalScale={1} {...toleranceForm.getInputProps('couch_angle_tol')} /></Grid.Col>
            </Grid>
            <Text size="sm" fw={600} mt="xs">Positional Tolerances (mm)</Text>
            <Grid>
              <Grid.Col span={4}><NumberInput label="Jaw X" step={0.5} decimalScale={1} {...toleranceForm.getInputProps('jaw_x_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="Jaw Y" step={0.5} decimalScale={1} {...toleranceForm.getInputProps('jaw_y_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="MLC" step={0.5} decimalScale={1} {...toleranceForm.getInputProps('mlc_tol')} /></Grid.Col>
            </Grid>
            <Text size="sm" fw={600} mt="xs">Delivery Tolerances</Text>
            <Grid>
              <Grid.Col span={4}><NumberInput label="MU" step={0.1} decimalScale={1} {...toleranceForm.getInputProps('mu_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="Dose Rate" step={1} {...toleranceForm.getInputProps('dose_rate_tol')} /></Grid.Col>
              <Grid.Col span={4}><NumberInput label="Energy" step={0.1} decimalScale={1} {...toleranceForm.getInputProps('energy_tol')} /></Grid.Col>
            </Grid>
            <Button type="submit" loading={createToleranceMut.isPending}>Create Tolerance Table</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
