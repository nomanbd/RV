import { useState, useCallback } from 'react';
import {
  Title, Card, Text, Stack, Alert, Grid, Badge, Group, Table, Button,
  Modal, Select, Progress, Divider, Stepper, TextInput,
  ActionIcon, Tooltip, ThemeIcon, Paper,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { useQuery } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import {
  RiPulseLine, RiAlertLine, RiShieldCheckLine, RiCheckLine,
  RiCloseLine, RiPlayLine, RiStopLine, RiUserLine,
  RiAlarmWarningLine, RiRefreshLine,
} from 'react-icons/ri';
import { useAppStore } from '../store';
import PatientBanner from '../components/common/PatientBanner';
import ElectronicSignature from '../components/common/ElectronicSignature';
import { planningApi } from '../api/planning';
import { machinesApi } from '../api/machines';
import type { PlanBeam } from '../types/planning';
import type { VerificationResult, ParameterCheck } from '../types/treatment';
import type { TreatmentMachine } from '../types/machine';

type SessionPhase = 'select_plan' | 'verify_patient' | 'setup' | 'treatment' | 'completed';

interface SimulatedBeamParams {
  gantry_angle: number;
  collimator_angle: number;
  couch_angle: number;
  jaw_x1: number;
  jaw_x2: number;
  jaw_y1: number;
  jaw_y2: number;
  energy: string;
  dose_rate: number;
  mu: number;
}

function StatusIcon({ passed }: { passed: boolean }) {
  return passed ? (
    <ThemeIcon color="green" size="sm" variant="light" radius="xl">
      <RiCheckLine size={12} />
    </ThemeIcon>
  ) : (
    <ThemeIcon color="red" size="sm" variant="light" radius="xl">
      <RiCloseLine size={12} />
    </ThemeIcon>
  );
}

function generateSimulatedActuals(beam: PlanBeam): SimulatedBeamParams {
  const jitter = (val: number | null, range: number) => {
    if (val === null) return 0;
    return +(val + (Math.random() - 0.5) * range).toFixed(2);
  };
  return {
    gantry_angle: jitter(beam.gantry_angle, 1.0),
    collimator_angle: jitter(beam.collimator_angle, 0.6),
    couch_angle: jitter(beam.couch_angle, 0.6),
    jaw_x1: jitter(beam.jaw_x1, 1.0),
    jaw_x2: jitter(beam.jaw_x2, 1.0),
    jaw_y1: jitter(beam.jaw_y1, 1.0),
    jaw_y2: jitter(beam.jaw_y2, 1.0),
    energy: beam.energy_label || '6 MV',
    dose_rate: jitter(beam.dose_rate_mu_per_min, 10),
    mu: jitter(beam.planned_mu, 0.5),
  };
}

function verifyBeamLocally(beam: PlanBeam, actuals: SimulatedBeamParams): VerificationResult {
  const checks: ParameterCheck[] = [];
  const addCheck = (name: string, planned: number | null, actual: number, tolerance: number) => {
    const p = planned ?? 0;
    const deviation = Math.abs(actual - p);
    checks.push({ name, planned: p, actual, tolerance, deviation: +deviation.toFixed(2), passed: deviation <= tolerance });
  };
  addCheck('Gantry Angle', beam.gantry_angle, actuals.gantry_angle, 1.0);
  addCheck('Collimator Angle', beam.collimator_angle, actuals.collimator_angle, 1.0);
  addCheck('Couch Angle', beam.couch_angle, actuals.couch_angle, 1.0);
  addCheck('Jaw X1', beam.jaw_x1, actuals.jaw_x1, 2.0);
  addCheck('Jaw X2', beam.jaw_x2, actuals.jaw_x2, 2.0);
  addCheck('Jaw Y1', beam.jaw_y1, actuals.jaw_y1, 2.0);
  addCheck('Jaw Y2', beam.jaw_y2, actuals.jaw_y2, 2.0);
  addCheck('Dose Rate', beam.dose_rate_mu_per_min, actuals.dose_rate, 20);
  addCheck('MU', beam.planned_mu, actuals.mu, 1.0);
  return {
    overall_pass: checks.every((c) => c.passed),
    checks,
    beam_number: beam.beam_number,
  };
}

export default function TreatmentConsolePage() {
  const { selectedPatient, user } = useAppStore();

  const [phase, setPhase] = useState<SessionPhase>('select_plan');
  const [selectedPlanId, setSelectedPlanId] = useState<string | null>(null);
  const [selectedMachineId, setSelectedMachineId] = useState<string | null>(null);
  const [verifyId1, setVerifyId1] = useState('');
  const [verifyId2, setVerifyId2] = useState('');
  const [beamResults, setBeamResults] = useState<Record<number, VerificationResult>>({});
  const [beamActuals, setBeamActuals] = useState<Record<number, SimulatedBeamParams>>({});
  const [activeBeamIndex, setActiveBeamIndex] = useState(0);
  const [beamDelivered, setBeamDelivered] = useState<Record<number, boolean>>({});
  const [overrideOpened, { open: openOverride, close: closeOverride }] = useDisclosure(false);
  const [overrideBeam, setOverrideBeam] = useState<number | null>(null);
  const [signatureOpened, { open: openSignature, close: closeSignature }] = useDisclosure(false);

  const { data: plans = [] } = useQuery({
    queryKey: ['patient-plans', selectedPatient?.id],
    queryFn: () => planningApi.listPlans({ patient_id: selectedPatient!.id, status: 'approved' }),
    enabled: !!selectedPatient,
  });

  const { data: machines = [] } = useQuery({
    queryKey: ['machines-active'],
    queryFn: () => machinesApi.listMachines('active'),
  });

  const selectedPlan = plans.find((p) => p.id === selectedPlanId);

  const handleStartSession = () => {
    if (!selectedPlanId || !selectedMachineId) return;
    setPhase('verify_patient');
    notifications.show({ title: 'Session Started', message: 'Proceed with patient verification', color: 'blue' });
  };

  const handleVerifyPatient = () => {
    if (selectedPatient) {
      const nameMatch = verifyId1.toLowerCase().includes(selectedPatient.last_name.toLowerCase());
      const mrnMatch = verifyId2 === selectedPatient.mrn;
      if (nameMatch && mrnMatch) {
        setPhase('setup');
        notifications.show({ title: 'Patient Verified', message: 'Two-identifier verification passed', color: 'green' });
      } else {
        notifications.show({ title: 'Verification Failed', message: 'Patient identifiers do not match', color: 'red' });
      }
    }
  };

  const handleVerifyBeam = useCallback((beam: PlanBeam) => {
    const actuals = generateSimulatedActuals(beam);
    const result = verifyBeamLocally(beam, actuals);
    setBeamActuals((prev) => ({ ...prev, [beam.beam_number]: actuals }));
    setBeamResults((prev) => ({ ...prev, [beam.beam_number]: result }));
  }, []);

  const handleVerifyAll = useCallback(() => {
    if (!selectedPlan?.beams) return;
    const newResults: Record<number, VerificationResult> = {};
    const newActuals: Record<number, SimulatedBeamParams> = {};
    selectedPlan.beams.forEach((beam) => {
      const actuals = generateSimulatedActuals(beam);
      const result = verifyBeamLocally(beam, actuals);
      newResults[beam.beam_number] = result;
      newActuals[beam.beam_number] = actuals;
    });
    setBeamResults(newResults);
    setBeamActuals(newActuals);
  }, [selectedPlan]);

  const handleBeamOn = (beamNum: number) => {
    setBeamDelivered((prev) => ({ ...prev, [beamNum]: true }));
    notifications.show({ title: `Beam ${beamNum} Delivered`, message: 'MU delivery complete', color: 'green' });
  };

  const handleOverride = (beamNum: number) => {
    setOverrideBeam(beamNum);
    openOverride();
  };

  const handleOverrideConfirm = () => {
    if (overrideBeam !== null) {
      setBeamResults((prev) => {
        const existing = prev[overrideBeam];
        if (!existing) return prev;
        return {
          ...prev,
          [overrideBeam]: {
            overall_pass: true,
            checks: existing.checks,
            beam_number: existing.beam_number,
          },
        };
      });
      closeOverride();
      notifications.show({ title: 'Override Approved', message: `Beam ${overrideBeam} verification overridden`, color: 'yellow' });
    }
  };

  const handleResetConsole = () => {
    setPhase('select_plan');
    setSelectedPlanId(null);
    setSelectedMachineId(null);
    setVerifyId1('');
    setVerifyId2('');
    setBeamResults({});
    setBeamActuals({});
    setActiveBeamIndex(0);
    setBeamDelivered({});
  };

  const allBeamsVerified = selectedPlan?.beams?.every((b) => beamResults[b.beam_number]?.overall_pass) ?? false;
  const allBeamsDelivered = selectedPlan?.beams?.every((b) => beamDelivered[b.beam_number]) ?? false;

  const getPhaseStep = () => {
    switch (phase) {
      case 'select_plan': return 0;
      case 'verify_patient': return 1;
      case 'setup': return 2;
      case 'treatment': return 3;
      case 'completed': return 4;
      default: return 0;
    }
  };

  if (!selectedPatient) {
    return (
      <Stack>
        <Group justify="space-between">
          <Title order={2}>Treatment Console</Title>
          <Badge color="yellow" size="lg" variant="light">No Patient Selected</Badge>
        </Group>
        <Alert icon={<RiAlertLine />} color="yellow" variant="light">
          Select a patient from the Patients page to begin treatment delivery.
        </Alert>
      </Stack>
    );
  }

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Treatment Console</Title>
        <Group>
          {phase === 'completed' ? (
            <Badge color="blue" size="lg" variant="light">Session Complete</Badge>
          ) : phase === 'treatment' ? (
            <Badge color="green" size="lg" variant="light">Treatment Active</Badge>
          ) : (
            <Badge color="yellow" size="lg" variant="light">Setup</Badge>
          )}
          {phase !== 'select_plan' && (
            <Tooltip label="Reset Console">
              <ActionIcon variant="subtle" color="gray" onClick={handleResetConsole}>
                <RiRefreshLine size={18} />
              </ActionIcon>
            </Tooltip>
          )}
        </Group>
      </Group>

      <PatientBanner patient={selectedPatient} />

      <Card withBorder p="md">
        <Stepper active={getPhaseStep()} size="sm">
          <Stepper.Step label="Select Plan" description="Choose plan & machine" />
          <Stepper.Step label="Verify Patient" description="Two-ID verification" />
          <Stepper.Step label="Setup" description="Verify beam parameters" />
          <Stepper.Step label="Treatment" description="Deliver beams" />
          <Stepper.Step label="Complete" description="Sign & finalize" />
        </Stepper>
      </Card>

      {/* Phase: Select Plan */}
      {phase === 'select_plan' && (
        <Grid>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card withBorder p="md">
              <Title order={4} mb="md">Select Treatment Plan</Title>
              <Select
                label="Approved Plan"
                placeholder="Choose a plan..."
                data={plans.map((p) => ({
                  value: p.id,
                  label: `${p.plan_label} — ${p.num_beams || 0} beams (v${p.version})`,
                }))}
                value={selectedPlanId}
                onChange={setSelectedPlanId}
              />
              {selectedPlan && (
                <Paper p="sm" mt="md" bg="gray.0" radius="sm">
                  <Text size="sm" fw={600}>{selectedPlan.plan_label}</Text>
                  <Text size="xs" c="dimmed">Status: {selectedPlan.status} | Beams: {selectedPlan.num_beams} | Fractions: {selectedPlan.num_fractions_planned}</Text>
                  {selectedPlan.beams?.map((beam) => (
                    <Text key={beam.id} size="xs" mt={4}>
                      Beam {beam.beam_number}: {beam.beam_name || beam.beam_type} — {beam.energy_label || `${beam.energy_mev} MeV`} | {beam.planned_mu?.toFixed(1)} MU | Gantry {beam.gantry_angle}°
                    </Text>
                  ))}
                </Paper>
              )}
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 6 }}>
            <Card withBorder p="md">
              <Title order={4} mb="md">Select Machine</Title>
              <Select
                label="Treatment Machine"
                placeholder="Choose a machine..."
                data={machines.map((m: TreatmentMachine) => ({
                  value: m.id,
                  label: `${m.name} — ${m.manufacturer || ''} ${m.model || ''}`,
                }))}
                value={selectedMachineId}
                onChange={setSelectedMachineId}
              />
              <Button
                fullWidth mt="lg" size="lg"
                disabled={!selectedPlanId || !selectedMachineId}
                onClick={handleStartSession}
              >
                Start Treatment Session
              </Button>
            </Card>
          </Grid.Col>
        </Grid>
      )}

      {/* Phase: Verify Patient */}
      {phase === 'verify_patient' && (
        <Card withBorder p="lg">
          <Group mb="md">
            <ThemeIcon size="lg" color="blue" variant="light"><RiUserLine size={20} /></ThemeIcon>
            <Title order={4}>Two-Identifier Patient Verification</Title>
          </Group>
          <Alert color="blue" variant="light" mb="md">
            Verify the patient using two independent identifiers before proceeding.
          </Alert>
          <Grid>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <TextInput label="Identifier 1: Patient Name" placeholder="Enter patient's last name..." value={verifyId1} onChange={(e) => setVerifyId1(e.currentTarget.value)} size="md" />
            </Grid.Col>
            <Grid.Col span={{ base: 12, md: 6 }}>
              <TextInput label="Identifier 2: MRN" placeholder="Enter MRN..." value={verifyId2} onChange={(e) => setVerifyId2(e.currentTarget.value)} size="md" />
            </Grid.Col>
          </Grid>
          <Group mt="lg">
            <Button size="lg" leftSection={<RiShieldCheckLine />} onClick={handleVerifyPatient} disabled={!verifyId1 || !verifyId2}>Verify Patient</Button>
            <Button variant="outline" onClick={() => setPhase('select_plan')}>Back</Button>
          </Group>
        </Card>
      )}

      {/* Phase: Setup — Beam Verification */}
      {phase === 'setup' && selectedPlan && (
        <Grid>
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card withBorder p="md">
              <Group justify="space-between" mb="md">
                <Title order={4}>Beam Parameter Verification</Title>
                <Button variant="light" leftSection={<RiShieldCheckLine size={16} />} onClick={handleVerifyAll}>
                  Verify All Beams
                </Button>
              </Group>
              <Table striped>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Beam</Table.Th>
                    <Table.Th>Parameter</Table.Th>
                    <Table.Th ta="right">Planned</Table.Th>
                    <Table.Th ta="right">Actual</Table.Th>
                    <Table.Th ta="right">Dev</Table.Th>
                    <Table.Th ta="right">Tol</Table.Th>
                    <Table.Th ta="center">Status</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {selectedPlan.beams?.map((beam) => {
                    const result = beamResults[beam.beam_number];
                    if (!result) {
                      return (
                        <Table.Tr key={beam.id}>
                          <Table.Td fw={600}>{beam.beam_number}: {beam.beam_name || beam.beam_type}</Table.Td>
                          <Table.Td colSpan={5}><Text c="dimmed" size="sm">Not yet verified</Text></Table.Td>
                          <Table.Td ta="center">
                            <Button size="xs" variant="light" onClick={() => handleVerifyBeam(beam)}>Verify</Button>
                          </Table.Td>
                        </Table.Tr>
                      );
                    }
                    return result.checks.map((check, ci) => (
                      <Table.Tr key={`${beam.id}-${ci}`} bg={!check.passed ? 'red.0' : undefined}>
                        {ci === 0 && (
                          <Table.Td rowSpan={result.checks.length} fw={600} style={{ verticalAlign: 'top' }}>
                            <Group gap={4}>
                              <Badge color={result.overall_pass ? 'green' : 'red'} size="xs">
                                {result.overall_pass ? 'PASS' : 'FAIL'}
                              </Badge>
                              <Text size="sm">{beam.beam_number}: {beam.beam_name || beam.beam_type}</Text>
                            </Group>
                          </Table.Td>
                        )}
                        <Table.Td><Text size="sm">{check.name}</Text></Table.Td>
                        <Table.Td ta="right"><Text size="sm">{check.planned.toFixed(1)}</Text></Table.Td>
                        <Table.Td ta="right"><Text size="sm" fw={500}>{check.actual.toFixed(1)}</Text></Table.Td>
                        <Table.Td ta="right"><Text size="sm" c={!check.passed ? 'red' : 'green'} fw={600}>{check.deviation.toFixed(2)}</Text></Table.Td>
                        <Table.Td ta="right"><Text size="sm" c="dimmed">{check.tolerance.toFixed(1)}</Text></Table.Td>
                        <Table.Td ta="center"><StatusIcon passed={check.passed} /></Table.Td>
                      </Table.Tr>
                    ));
                  })}
                </Table.Tbody>
              </Table>
              {Object.entries(beamResults).some(([, r]) => !r.overall_pass) && (
                <Alert color="red" variant="light" mt="md" icon={<RiAlarmWarningLine />}>
                  <Group justify="space-between">
                    <Text size="sm">One or more beams failed verification. Override requires physicist signature.</Text>
                    <Button size="xs" color="red" variant="outline" onClick={() => {
                      const failedBeam = Object.entries(beamResults).find(([, r]) => !r.overall_pass);
                      if (failedBeam) handleOverride(Number(failedBeam[0]));
                    }}>Override with Signature</Button>
                  </Group>
                </Alert>
              )}
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Stack>
              <Card withBorder p="md">
                <Title order={4} mb="md">Plan Summary</Title>
                <Text size="sm" fw={600}>{selectedPlan.plan_label}</Text>
                <Text size="xs" c="dimmed" mb="xs">Version {selectedPlan.version}</Text>
                <Divider my="xs" />
                <Text size="sm">Beams: {selectedPlan.beams?.length || 0}</Text>
                <Text size="sm">Fractions Planned: {selectedPlan.num_fractions_planned || '-'}</Text>
                <Text size="sm">Verified: {Object.values(beamResults).filter((r) => r.overall_pass).length} / {selectedPlan.beams?.length || 0}</Text>
                <Progress value={((Object.values(beamResults).filter((r) => r.overall_pass).length) / (selectedPlan.beams?.length || 1)) * 100} color={allBeamsVerified ? 'green' : 'blue'} mt="xs" size="lg" />
              </Card>
              <Card withBorder p="md">
                <Title order={4} mb="md">Session Control</Title>
                <Button fullWidth size="lg" color="green" leftSection={<RiPlayLine />} disabled={!allBeamsVerified} onClick={() => setPhase('treatment')}>
                  Proceed to Treatment
                </Button>
                <Button fullWidth mt="sm" variant="outline" onClick={() => setPhase('verify_patient')}>Back to Verification</Button>
              </Card>
            </Stack>
          </Grid.Col>
        </Grid>
      )}

      {/* Phase: Treatment — Beam Delivery */}
      {phase === 'treatment' && selectedPlan && (
        <Grid>
          <Grid.Col span={{ base: 12, md: 8 }}>
            <Card withBorder p="md">
              <Title order={4} mb="md">Beam Delivery</Title>
              <Stack>
                {selectedPlan.beams?.map((beam, idx) => {
                  const actuals = beamActuals[beam.beam_number];
                  const delivered = beamDelivered[beam.beam_number];
                  return (
                    <Paper key={beam.id} withBorder p="md" bg={delivered ? 'green.0' : activeBeamIndex === idx ? 'blue.0' : undefined}>
                      <Group justify="space-between" mb="xs">
                        <Group>
                          <Badge color={delivered ? 'green' : activeBeamIndex === idx ? 'blue' : 'gray'}>Beam {beam.beam_number}</Badge>
                          <Text fw={600} size="sm">{beam.beam_name || beam.beam_type}</Text>
                          <Text size="xs" c="dimmed">{beam.energy_label || `${beam.energy_mev} MeV`} | Gantry {beam.gantry_angle}°</Text>
                        </Group>
                        {delivered ? (
                          <Badge color="green" size="lg">DELIVERED</Badge>
                        ) : (
                          <Button color="green" size="sm" leftSection={<RiPulseLine />} disabled={activeBeamIndex !== idx} onClick={() => {
                            handleBeamOn(beam.beam_number);
                            if (idx < (selectedPlan.beams?.length || 0) - 1) setActiveBeamIndex(idx + 1);
                          }}>
                            BEAM ON — {beam.planned_mu?.toFixed(1)} MU
                          </Button>
                        )}
                      </Group>
                      {delivered && actuals && (
                        <Group gap="lg">
                          <Text size="xs">Delivered MU: {actuals.mu.toFixed(1)}</Text>
                          <Text size="xs">Dose Rate: {actuals.dose_rate.toFixed(0)} MU/min</Text>
                          <Text size="xs">Gantry: {actuals.gantry_angle.toFixed(1)}°</Text>
                        </Group>
                      )}
                    </Paper>
                  );
                })}
              </Stack>
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, md: 4 }}>
            <Stack>
              <Card withBorder p="md">
                <Title order={4} mb="md">Delivery Progress</Title>
                <Text size="sm" mb="xs">Beams delivered: {Object.values(beamDelivered).filter(Boolean).length} / {selectedPlan.beams?.length || 0}</Text>
                <Progress value={(Object.values(beamDelivered).filter(Boolean).length / (selectedPlan.beams?.length || 1)) * 100} color={allBeamsDelivered ? 'green' : 'blue'} size="xl" mb="md" />
                <Text size="xs" c="dimmed">Total MU: {selectedPlan.beams?.reduce((sum, b) => sum + (b.planned_mu || 0), 0).toFixed(1)}</Text>
              </Card>
              <Card withBorder p="md">
                <Title order={4} mb="md">Session Control</Title>
                <Stack>
                  <Button fullWidth size="lg" color="red" variant="outline" leftSection={<RiStopLine />} onClick={() => notifications.show({ title: 'Beam Interrupted', message: 'Treatment paused', color: 'red' })}>
                    BEAM OFF / INTERRUPT
                  </Button>
                  <Button fullWidth size="lg" color="green" disabled={!allBeamsDelivered} leftSection={<RiShieldCheckLine />} onClick={openSignature}>
                    Complete Session
                  </Button>
                </Stack>
              </Card>
              <Card withBorder p="md">
                <Title order={5} mb="xs">Therapist</Title>
                <Text size="sm">{user?.first_name} {user?.last_name}</Text>
              </Card>
            </Stack>
          </Grid.Col>
        </Grid>
      )}

      {/* Phase: Completed */}
      {phase === 'completed' && (
        <Card withBorder p="xl">
          <Stack align="center">
            <ThemeIcon size={80} color="green" variant="light" radius="xl"><RiCheckLine size={40} /></ThemeIcon>
            <Title order={3}>Treatment Session Complete</Title>
            <Text c="dimmed" ta="center">All beams delivered successfully. Session signed and recorded.</Text>
            <Button variant="light" onClick={handleResetConsole}>New Session</Button>
          </Stack>
        </Card>
      )}

      {/* Override Modal */}
      <Modal opened={overrideOpened} onClose={closeOverride} title="Override Beam Verification" size="md">
        <Stack>
          <Alert color="red" variant="light">Beam {overrideBeam} failed parameter verification. A physicist must authorize this override.</Alert>
          {overrideBeam !== null && beamResults[overrideBeam] && (
            <Table>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Parameter</Table.Th>
                  <Table.Th>Deviation</Table.Th>
                  <Table.Th>Tolerance</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {beamResults[overrideBeam].checks.filter((c) => !c.passed).map((check, i) => (
                  <Table.Tr key={i}>
                    <Table.Td>{check.name}</Table.Td>
                    <Table.Td c="red" fw={600}>{check.deviation.toFixed(2)}</Table.Td>
                    <Table.Td>{check.tolerance.toFixed(1)}</Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
          <Button color="red" onClick={handleOverrideConfirm}>Authorize Override (Physicist Signature)</Button>
        </Stack>
      </Modal>

      {/* Completion Signature */}
      <ElectronicSignature
        opened={signatureOpened}
        onClose={closeSignature}
        onSigned={() => {
          closeSignature();
          setPhase('completed');
          notifications.show({ title: 'Session Complete', message: 'Treatment session recorded', color: 'green' });
        }}
        entityType="treatment_session"
        entityId={selectedPlanId || 'session'}
        title="Sign Treatment Session"
        requiredMeaning="verification"
      />
    </Stack>
  );
}
