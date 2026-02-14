import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Title, TextInput, Button, Table, Group, Badge, Card, Stack,
  ActionIcon, Modal, Loader, Center, Text, Grid, Select,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useDisclosure } from '@mantine/hooks';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { RiSearchLine, RiAddLine, RiEyeLine } from 'react-icons/ri';
import { patientsApi } from '../api/patients';
import { useAppStore } from '../store';
import type { Patient, PatientCreate } from '../types/patient';

export default function PatientListPage() {
  const [search, setSearch] = useState('');
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { setSelectedPatient } = useAppStore();

  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients', search],
    queryFn: () => patientsApi.list({ q: search || undefined }),
  });

  const form = useForm<PatientCreate>({
    initialValues: {
      mrn: '',
      first_name: '',
      last_name: '',
      date_of_birth: '',
      sex: 'M',
      middle_name: '',
      phone_primary: '',
      email: '',
      address_line1: '',
      city: '',
      state: '',
      postal_code: '',
      notes: '',
    },
    validate: {
      mrn: (v) => (!v ? 'MRN is required' : null),
      first_name: (v) => (!v ? 'First name is required' : null),
      last_name: (v) => (!v ? 'Last name is required' : null),
      date_of_birth: (v) => (!v ? 'Date of birth is required' : null),
      sex: (v) => (!v ? 'Sex is required' : null),
    },
  });

  const createMutation = useMutation({
    mutationFn: (data: PatientCreate) => patientsApi.create(data),
    onSuccess: (newPatient) => {
      queryClient.invalidateQueries({ queryKey: ['patients'] });
      closeCreate();
      form.reset();
      notifications.show({ title: 'Patient Registered', message: `${newPatient.last_name}, ${newPatient.first_name} (MRN: ${newPatient.mrn})`, color: 'green' });
      setSelectedPatient(newPatient);
      navigate(`/patients/${newPatient.id}`);
    },
    onError: (err: unknown) => {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      notifications.show({ title: 'Registration Failed', message: message || 'Could not register patient', color: 'red' });
    },
  });

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    navigate(`/patients/${patient.id}`);
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Patients</Title>
        <Button leftSection={<RiAddLine />} onClick={openCreate}>Register Patient</Button>
      </Group>

      <Card withBorder p="md">
        <TextInput
          placeholder="Search by MRN, name, or DICOM ID..."
          leftSection={<RiSearchLine />}
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          mb="md"
        />
        {isLoading ? (
          <Center py="xl"><Loader /></Center>
        ) : patients && patients.length > 0 ? (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>MRN</Table.Th>
                <Table.Th>Name</Table.Th>
                <Table.Th>Date of Birth</Table.Th>
                <Table.Th>Sex</Table.Th>
                <Table.Th>Status</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {patients.map((patient) => (
                <Table.Tr key={patient.id} style={{ cursor: 'pointer' }} onClick={() => handleSelectPatient(patient)}>
                  <Table.Td fw={600}>{patient.mrn}</Table.Td>
                  <Table.Td>{patient.last_name}, {patient.first_name}{patient.middle_name ? ` ${patient.middle_name}` : ''}</Table.Td>
                  <Table.Td>{patient.date_of_birth}</Table.Td>
                  <Table.Td>{patient.sex}</Table.Td>
                  <Table.Td><Badge color={patient.is_active ? 'green' : 'gray'} size="sm">{patient.is_active ? 'Active' : 'Inactive'}</Badge></Table.Td>
                  <Table.Td>
                    <ActionIcon variant="subtle" onClick={(e) => { e.stopPropagation(); handleSelectPatient(patient); }}>
                      <RiEyeLine />
                    </ActionIcon>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : (
          <Text c="dimmed" ta="center" py="xl">No patients found. Register a new patient to get started.</Text>
        )}
      </Card>

      {/* Patient Registration Modal */}
      <Modal opened={createOpened} onClose={closeCreate} title="Register New Patient" size="lg">
        <form onSubmit={form.onSubmit((values) => createMutation.mutate(values))}>
          <Stack>
            <TextInput label="MRN" placeholder="Medical Record Number" required {...form.getInputProps('mrn')} />
            <Grid>
              <Grid.Col span={4}>
                <TextInput label="First Name" required {...form.getInputProps('first_name')} />
              </Grid.Col>
              <Grid.Col span={4}>
                <TextInput label="Middle Name" {...form.getInputProps('middle_name')} />
              </Grid.Col>
              <Grid.Col span={4}>
                <TextInput label="Last Name" required {...form.getInputProps('last_name')} />
              </Grid.Col>
            </Grid>
            <Grid>
              <Grid.Col span={6}>
                <TextInput label="Date of Birth" type="date" required {...form.getInputProps('date_of_birth')} />
              </Grid.Col>
              <Grid.Col span={6}>
                <Select
                  label="Sex"
                  data={[
                    { value: 'M', label: 'Male' },
                    { value: 'F', label: 'Female' },
                    { value: 'O', label: 'Other' },
                  ]}
                  required
                  {...form.getInputProps('sex')}
                />
              </Grid.Col>
            </Grid>
            <Grid>
              <Grid.Col span={6}>
                <TextInput label="Phone" placeholder="(555) 123-4567" {...form.getInputProps('phone_primary')} />
              </Grid.Col>
              <Grid.Col span={6}>
                <TextInput label="Email" type="email" {...form.getInputProps('email')} />
              </Grid.Col>
            </Grid>
            <TextInput label="Address" placeholder="Street address" {...form.getInputProps('address_line1')} />
            <Grid>
              <Grid.Col span={4}>
                <TextInput label="City" {...form.getInputProps('city')} />
              </Grid.Col>
              <Grid.Col span={4}>
                <TextInput label="State" {...form.getInputProps('state')} />
              </Grid.Col>
              <Grid.Col span={4}>
                <TextInput label="Postal Code" {...form.getInputProps('postal_code')} />
              </Grid.Col>
            </Grid>
            <TextInput label="Notes" {...form.getInputProps('notes')} />
            <Group justify="flex-end">
              <Button variant="subtle" onClick={closeCreate}>Cancel</Button>
              <Button type="submit" loading={createMutation.isPending}>Register Patient</Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
