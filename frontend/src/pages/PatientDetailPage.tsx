import { useParams } from 'react-router-dom';
import {
  Title,
  Tabs,
  Card,
  Stack,
  Text,
  Group,
  Badge,
  Table,
  Loader,
  Center,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  RiUserLine,
  RiFileList3Line,
  RiPulseLine,
  RiImage2Line,
  RiTimeLine,
} from 'react-icons/ri';
import { patientsApi } from '../api/patients';
import PatientBanner from '../components/common/PatientBanner';
import { useAppStore } from '../store';

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { setSelectedPatient } = useAppStore();

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientsApi.get(id!),
    enabled: !!id,
  });

  if (isLoading) {
    return (
      <Center py="xl">
        <Loader size="lg" />
      </Center>
    );
  }

  if (!patient) {
    return <Text>Patient not found.</Text>;
  }

  // Set as selected patient
  if (patient) {
    setSelectedPatient(patient);
  }

  return (
    <Stack>
      <PatientBanner patient={patient} />

      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<RiUserLine size={16} />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="plans" leftSection={<RiFileList3Line size={16} />}>
            Treatment Plans
          </Tabs.Tab>
          <Tabs.Tab value="treatment" leftSection={<RiPulseLine size={16} />}>
            Treatment History
          </Tabs.Tab>
          <Tabs.Tab value="images" leftSection={<RiImage2Line size={16} />}>
            Images
          </Tabs.Tab>
          <Tabs.Tab value="timeline" leftSection={<RiTimeLine size={16} />}>
            Timeline
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="overview" pt="md">
          <Card withBorder p="md">
            <Title order={4} mb="md">Demographics</Title>
            <Table>
              <Table.Tbody>
                <Table.Tr>
                  <Table.Td fw={600} w={200}>Full Name</Table.Td>
                  <Table.Td>
                    {patient.last_name}, {patient.first_name}
                    {patient.middle_name ? ` ${patient.middle_name}` : ''}
                  </Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>MRN</Table.Td>
                  <Table.Td>{patient.mrn}</Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>Date of Birth</Table.Td>
                  <Table.Td>{patient.date_of_birth}</Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>Sex</Table.Td>
                  <Table.Td>{patient.sex}</Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>Phone</Table.Td>
                  <Table.Td>{patient.phone_primary || '—'}</Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>Email</Table.Td>
                  <Table.Td>{patient.email || '—'}</Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>Address</Table.Td>
                  <Table.Td>
                    {patient.address_line1 || '—'}
                    {patient.city ? `, ${patient.city}` : ''}
                    {patient.state ? `, ${patient.state}` : ''}
                    {patient.postal_code ? ` ${patient.postal_code}` : ''}
                  </Table.Td>
                </Table.Tr>
                <Table.Tr>
                  <Table.Td fw={600}>DICOM Patient ID</Table.Td>
                  <Table.Td>{patient.dicom_patient_id || '—'}</Table.Td>
                </Table.Tr>
              </Table.Tbody>
            </Table>
          </Card>

          {patient.diagnoses && patient.diagnoses.length > 0 && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Diagnoses</Title>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>ICD-10</Table.Th>
                    <Table.Th>Description</Table.Th>
                    <Table.Th>Site</Table.Th>
                    <Table.Th>Laterality</Table.Th>
                    <Table.Th>Date</Table.Th>
                    <Table.Th>Primary</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {patient.diagnoses.map((dx) => (
                    <Table.Tr key={dx.id}>
                      <Table.Td fw={600}>{dx.icd10_code}</Table.Td>
                      <Table.Td>{dx.description}</Table.Td>
                      <Table.Td>{dx.site || '—'}</Table.Td>
                      <Table.Td>{dx.laterality || '—'}</Table.Td>
                      <Table.Td>{dx.diagnosis_date || '—'}</Table.Td>
                      <Table.Td>
                        {dx.is_primary && <Badge color="blue" size="xs">Primary</Badge>}
                      </Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Card>
          )}

          {patient.allergies && patient.allergies.length > 0 && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Allergies</Title>
              <Group>
                {patient.allergies.map((allergy) => (
                  <Badge key={allergy.id} color="red" variant="light" size="lg">
                    {allergy.allergen}
                    {allergy.severity ? ` (${allergy.severity})` : ''}
                  </Badge>
                ))}
              </Group>
            </Card>
          )}

          {patient.notes && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Notes</Title>
              <Text>{patient.notes}</Text>
            </Card>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="plans" pt="md">
          <Card withBorder p="md">
            <Text c="dimmed" ta="center" py="xl">
              Treatment plans will be displayed here after DICOM import is implemented.
            </Text>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="treatment" pt="md">
          <Card withBorder p="md">
            <Text c="dimmed" ta="center" py="xl">
              Treatment delivery history will be displayed here.
            </Text>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="images" pt="md">
          <Card withBorder p="md">
            <Text c="dimmed" ta="center" py="xl">
              Patient images will be displayed here.
            </Text>
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="timeline" pt="md">
          <Card withBorder p="md">
            <Text c="dimmed" ta="center" py="xl">
              Patient treatment timeline will be displayed here.
            </Text>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
