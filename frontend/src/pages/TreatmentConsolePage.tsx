import { Title, Card, Text, Stack, Alert, Grid, Badge, Group, Table, Button } from '@mantine/core';
import { RiPulseLine, RiAlertLine, RiShieldCheckLine } from 'react-icons/ri';
import { useAppStore } from '../store';
import PatientBanner from '../components/common/PatientBanner';

export default function TreatmentConsolePage() {
  const { selectedPatient } = useAppStore();

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Treatment Console</Title>
        <Badge color="green" size="lg" variant="light">
          System Ready
        </Badge>
      </Group>

      {!selectedPatient ? (
        <Alert icon={<RiAlertLine />} color="yellow" variant="light">
          Select a patient from the Patients page to begin treatment delivery.
        </Alert>
      ) : (
        <>
          <PatientBanner patient={selectedPatient} />

          <Grid>
            <Grid.Col span={{ base: 12, md: 8 }}>
              <Card withBorder p="md">
                <Title order={4} mb="md">Beam Parameter Verification</Title>
                <Table>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Parameter</Table.Th>
                      <Table.Th>Planned</Table.Th>
                      <Table.Th>Actual</Table.Th>
                      <Table.Th>Deviation</Table.Th>
                      <Table.Th>Tolerance</Table.Th>
                      <Table.Th>Status</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    <Table.Tr>
                      <Table.Td colSpan={6}>
                        <Text c="dimmed" ta="center" py="md">
                          Load a treatment plan to begin beam parameter verification.
                        </Text>
                      </Table.Td>
                    </Table.Tr>
                  </Table.Tbody>
                </Table>
              </Card>
            </Grid.Col>

            <Grid.Col span={{ base: 12, md: 4 }}>
              <Stack>
                <Card withBorder p="md">
                  <Title order={4} mb="md">Fraction Progress</Title>
                  <Text c="dimmed" ta="center" py="md">
                    No active treatment course.
                  </Text>
                </Card>

                <Card withBorder p="md">
                  <Title order={4} mb="md">Beam Control</Title>
                  <Stack>
                    <Button
                      fullWidth
                      size="lg"
                      color="green"
                      leftSection={<RiPulseLine />}
                      disabled
                    >
                      BEAM ON
                    </Button>
                    <Button
                      fullWidth
                      size="lg"
                      color="red"
                      variant="outline"
                      disabled
                    >
                      BEAM OFF
                    </Button>
                    <Button
                      fullWidth
                      variant="outline"
                      leftSection={<RiShieldCheckLine />}
                      disabled
                    >
                      Verify All Beams
                    </Button>
                  </Stack>
                </Card>
              </Stack>
            </Grid.Col>
          </Grid>
        </>
      )}
    </Stack>
  );
}
