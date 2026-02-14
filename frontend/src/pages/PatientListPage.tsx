import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Title,
  TextInput,
  Button,
  Table,
  Group,
  Badge,
  Card,
  Stack,
  ActionIcon,
  Modal,
  Loader,
  Center,
  Text,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { RiSearchLine, RiAddLine, RiEyeLine } from 'react-icons/ri';
import { patientsApi } from '../api/patients';
import { useAppStore } from '../store';
import type { Patient } from '../types/patient';

export default function PatientListPage() {
  const [search, setSearch] = useState('');
  const [createOpened, { open: openCreate, close: closeCreate }] = useDisclosure(false);
  const navigate = useNavigate();
  const { setSelectedPatient } = useAppStore();

  const { data: patients, isLoading } = useQuery({
    queryKey: ['patients', search],
    queryFn: () => patientsApi.list({ q: search || undefined }),
  });

  const handleSelectPatient = (patient: Patient) => {
    setSelectedPatient(patient);
    navigate(`/patients/${patient.id}`);
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Patients</Title>
        <Button leftSection={<RiAddLine />} onClick={openCreate}>
          Register Patient
        </Button>
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
          <Center py="xl">
            <Loader />
          </Center>
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
                <Table.Tr
                  key={patient.id}
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleSelectPatient(patient)}
                >
                  <Table.Td fw={600}>{patient.mrn}</Table.Td>
                  <Table.Td>
                    {patient.last_name}, {patient.first_name}
                    {patient.middle_name ? ` ${patient.middle_name}` : ''}
                  </Table.Td>
                  <Table.Td>{patient.date_of_birth}</Table.Td>
                  <Table.Td>{patient.sex}</Table.Td>
                  <Table.Td>
                    <Badge color={patient.is_active ? 'green' : 'gray'} size="sm">
                      {patient.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                  </Table.Td>
                  <Table.Td>
                    <ActionIcon
                      variant="subtle"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectPatient(patient);
                      }}
                    >
                      <RiEyeLine />
                    </ActionIcon>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        ) : (
          <Text c="dimmed" ta="center" py="xl">
            No patients found. Register a new patient to get started.
          </Text>
        )}
      </Card>

      <Modal opened={createOpened} onClose={closeCreate} title="Register New Patient" size="lg">
        <Text c="dimmed" ta="center" py="xl">
          Patient registration form will be implemented here.
        </Text>
      </Modal>
    </Stack>
  );
}
