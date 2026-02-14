import { Badge, Card, Group, Text, ActionIcon } from '@mantine/core';
import { RiCloseLine } from 'react-icons/ri';
import type { Patient } from '../../types/patient';
import { useAppStore } from '../../store';

interface PatientBannerProps {
  patient: Patient;
  compact?: boolean;
}

export default function PatientBanner({ patient, compact }: PatientBannerProps) {
  const { setSelectedPatient } = useAppStore();

  if (compact) {
    return (
      <Group gap="xs" style={{ cursor: 'pointer' }}>
        <Badge color="blue" variant="filled" size="sm">
          {patient.mrn}
        </Badge>
        <Text size="sm" fw={500}>
          {patient.last_name}, {patient.first_name}
        </Text>
        <ActionIcon
          size="xs"
          variant="subtle"
          onClick={(e) => {
            e.stopPropagation();
            setSelectedPatient(null);
          }}
        >
          <RiCloseLine />
        </ActionIcon>
      </Group>
    );
  }

  return (
    <Card withBorder p="sm" mb="md" bg="blue.0">
      <Group justify="space-between">
        <Group>
          <div>
            <Text size="lg" fw={700}>
              {patient.last_name}, {patient.first_name}
              {patient.middle_name ? ` ${patient.middle_name}` : ''}
            </Text>
            <Group gap="md">
              <Text size="sm" c="dimmed">
                MRN: <Text span fw={600}>{patient.mrn}</Text>
              </Text>
              <Text size="sm" c="dimmed">
                DOB: <Text span fw={600}>{patient.date_of_birth}</Text>
              </Text>
              <Text size="sm" c="dimmed">
                Sex: <Text span fw={600}>{patient.sex}</Text>
              </Text>
            </Group>
          </div>
        </Group>
        <Group>
          <Badge color={patient.is_active ? 'green' : 'gray'}>
            {patient.is_active ? 'Active' : 'Inactive'}
          </Badge>
          <ActionIcon
            variant="subtle"
            onClick={() => setSelectedPatient(null)}
          >
            <RiCloseLine />
          </ActionIcon>
        </Group>
      </Group>
    </Card>
  );
}
