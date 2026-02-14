import { useState } from 'react';
import {
  Title,
  Stack,
  Tabs,
  Card,
  Group,
  Text,
  Badge,
  Button,
  Table,
  Modal,
  TextInput,
  Select,
  Switch,
  Loader,
  Center,
  Alert,
  Paper,
  SimpleGrid,
  ThemeIcon,
  ActionIcon,
  Tooltip,
  PasswordInput,
  NumberInput,
  Divider,
  Code,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { notifications } from '@mantine/notifications';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  RiAddLine,
  RiTestTubeLine,
  RiDeleteBinLine,
  RiRefreshLine,
  RiSearchLine,
  RiDownloadLine,
  RiCalendarLine,
  RiHistoryLine,
  RiPlugLine,
  RiUserSearchLine,
} from 'react-icons/ri';
import { oisApi } from '../api/ois';
import type {
  OISConnectionCreate,
  OISPatientResult,
  OISPlanResult,
} from '../types/ois';

function ConnectionStatusBadge({ status }: { status: string }) {
  const colorMap: Record<string, string> = {
    connected: 'green',
    disconnected: 'gray',
    error: 'red',
    testing: 'yellow',
  };
  return (
    <Badge color={colorMap[status] || 'gray'} variant="light" size="sm">
      {status}
    </Badge>
  );
}

function OISTypeBadge({ type }: { type: string }) {
  const colorMap: Record<string, string> = {
    aria: 'blue',
    raycare: 'violet',
    generic_fhir: 'teal',
  };
  const labelMap: Record<string, string> = {
    aria: 'Varian ARIA',
    raycare: 'RayCare',
    generic_fhir: 'HL7 FHIR',
  };
  return (
    <Badge color={colorMap[type] || 'gray'} variant="filled" size="sm">
      {labelMap[type] || type}
    </Badge>
  );
}

// ── Connections Tab ──────────────────────────────────────────────────

function ConnectionsTab() {
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [testingId, setTestingId] = useState<string | null>(null);

  const { data: connections = [], isLoading } = useQuery({
    queryKey: ['ois-connections'],
    queryFn: () => oisApi.listConnections(),
  });

  const createMutation = useMutation({
    mutationFn: (data: OISConnectionCreate) => oisApi.createConnection(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ois-connections'] });
      setCreateOpen(false);
      notifications.show({ title: 'Connection Created', message: 'OIS connection added successfully', color: 'green' });
    },
    onError: () => {
      notifications.show({ title: 'Error', message: 'Failed to create connection', color: 'red' });
    },
  });

  const testMutation = useMutation({
    mutationFn: (id: string) => oisApi.testConnection(id),
    onSuccess: (result) => {
      setTestingId(null);
      queryClient.invalidateQueries({ queryKey: ['ois-connections'] });
      notifications.show({
        title: result.success ? 'Connected' : 'Connection Failed',
        message: `${result.message}${result.response_time_ms ? ` (${result.response_time_ms}ms)` : ''}`,
        color: result.success ? 'green' : 'red',
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => oisApi.deleteConnection(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ois-connections'] });
      notifications.show({ title: 'Deleted', message: 'Connection removed', color: 'orange' });
    },
  });

  const form = useForm<OISConnectionCreate>({
    initialValues: {
      name: '',
      ois_type: 'aria',
      base_url: '',
      auth_type: 'oauth2',
      client_id: '',
      client_secret: '',
      api_key: '',
      username: '',
      password: '',
      fhir_base_url: '',
      dicom_ae_title: '',
      dicom_host: '',
      dicom_port: undefined,
      is_primary: false,
    },
  });

  if (isLoading) return <Center py="xl"><Loader /></Center>;

  return (
    <Stack>
      <Group justify="space-between">
        <Text size="sm" c="dimmed">Manage connections to external Oncology Information Systems</Text>
        <Button leftSection={<RiAddLine size={16} />} onClick={() => setCreateOpen(true)}>
          Add Connection
        </Button>
      </Group>

      {connections.length === 0 ? (
        <Card withBorder p="xl">
          <Center>
            <Stack align="center" gap="xs">
              <ThemeIcon size={48} variant="light" color="gray" radius="xl"><RiPlugLine size={24} /></ThemeIcon>
              <Text fw={500}>No OIS Connections</Text>
              <Text size="sm" c="dimmed">Add a connection to ARIA, RayCare, or a FHIR server to get started.</Text>
            </Stack>
          </Center>
        </Card>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Name</Table.Th>
              <Table.Th>Type</Table.Th>
              <Table.Th>URL</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Last Connected</Table.Th>
              <Table.Th>Primary</Table.Th>
              <Table.Th>Actions</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {connections.map((conn) => (
              <Table.Tr key={conn.id}>
                <Table.Td><Text fw={500}>{conn.name}</Text></Table.Td>
                <Table.Td><OISTypeBadge type={conn.ois_type} /></Table.Td>
                <Table.Td><Code>{conn.base_url}</Code></Table.Td>
                <Table.Td><ConnectionStatusBadge status={conn.connection_status} /></Table.Td>
                <Table.Td>
                  <Text size="sm" c="dimmed">
                    {conn.last_connected_at
                      ? new Date(conn.last_connected_at).toLocaleString()
                      : 'Never'}
                  </Text>
                </Table.Td>
                <Table.Td>
                  {conn.is_primary && <Badge color="blue" variant="light" size="xs">Primary</Badge>}
                </Table.Td>
                <Table.Td>
                  <Group gap="xs">
                    <Tooltip label="Test Connection">
                      <ActionIcon
                        variant="light"
                        color="blue"
                        loading={testingId === conn.id}
                        onClick={() => {
                          setTestingId(conn.id);
                          testMutation.mutate(conn.id);
                        }}
                      >
                        <RiTestTubeLine size={16} />
                      </ActionIcon>
                    </Tooltip>
                    <Tooltip label="Delete">
                      <ActionIcon
                        variant="light"
                        color="red"
                        onClick={() => {
                          if (confirm('Delete this OIS connection?')) {
                            deleteMutation.mutate(conn.id);
                          }
                        }}
                      >
                        <RiDeleteBinLine size={16} />
                      </ActionIcon>
                    </Tooltip>
                  </Group>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}

      {/* Create Connection Modal */}
      <Modal
        opened={createOpen}
        onClose={() => setCreateOpen(false)}
        title="Add OIS Connection"
        size="lg"
      >
        <form onSubmit={form.onSubmit((values) => createMutation.mutate(values))}>
          <Stack>
            <TextInput
              label="Connection Name"
              placeholder="e.g., Main ARIA Server"
              required
              {...form.getInputProps('name')}
            />

            <Select
              label="OIS Type"
              data={[
                { value: 'aria', label: 'Varian ARIA' },
                { value: 'raycare', label: 'RaySearch RayCare' },
                { value: 'generic_fhir', label: 'Generic HL7 FHIR' },
              ]}
              required
              {...form.getInputProps('ois_type')}
            />

            <TextInput
              label="Base URL"
              placeholder="https://aria-server.hospital.org"
              required
              {...form.getInputProps('base_url')}
            />

            <Divider label="Authentication" labelPosition="center" />

            <Select
              label="Auth Type"
              data={[
                { value: 'oauth2', label: 'OAuth 2.0 (Recommended)' },
                { value: 'api_key', label: 'API Key' },
                { value: 'basic', label: 'Basic Auth' },
                { value: 'certificate', label: 'Client Certificate' },
              ]}
              {...form.getInputProps('auth_type')}
            />

            {form.values.auth_type === 'oauth2' && (
              <>
                <TextInput label="Client ID" placeholder="client-id" {...form.getInputProps('client_id')} />
                <PasswordInput label="Client Secret" placeholder="client-secret" {...form.getInputProps('client_secret')} />
              </>
            )}

            {form.values.auth_type === 'api_key' && (
              <PasswordInput label="API Key" placeholder="your-api-key" {...form.getInputProps('api_key')} />
            )}

            {form.values.auth_type === 'basic' && (
              <>
                <TextInput label="Username" {...form.getInputProps('username')} />
                <PasswordInput label="Password" {...form.getInputProps('password')} />
              </>
            )}

            <Divider label="Optional Settings" labelPosition="center" />

            {form.values.ois_type === 'generic_fhir' && (
              <TextInput
                label="FHIR Base URL"
                placeholder="https://fhir.hospital.org/r4"
                {...form.getInputProps('fhir_base_url')}
              />
            )}

            <Group grow>
              <TextInput label="DICOM AE Title" placeholder="ARIA_AE" {...form.getInputProps('dicom_ae_title')} />
              <TextInput label="DICOM Host" placeholder="aria-dicom.hospital.org" {...form.getInputProps('dicom_host')} />
              <NumberInput label="DICOM Port" placeholder="104" {...form.getInputProps('dicom_port')} />
            </Group>

            <Switch label="Set as primary OIS connection" {...form.getInputProps('is_primary', { type: 'checkbox' })} />

            <Group justify="flex-end">
              <Button variant="default" onClick={() => setCreateOpen(false)}>Cancel</Button>
              <Button type="submit" loading={createMutation.isPending}>Create Connection</Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}

// ── Patient Lookup Tab ──────────────────────────────────────────────

function PatientLookupTab() {
  const [selectedConn, setSelectedConn] = useState<string | null>(null);
  const [patients, setPatients] = useState<OISPatientResult[]>([]);
  const [plans, setPlans] = useState<{ patientId: string; plans: OISPlanResult[] } | null>(null);

  const { data: connections = [] } = useQuery({
    queryKey: ['ois-connections'],
    queryFn: () => oisApi.listConnections(true),
  });

  const form = useForm({
    initialValues: { mrn: '', first_name: '', last_name: '', date_of_birth: '' },
  });

  const lookupMutation = useMutation({
    mutationFn: (params: { mrn?: string; first_name?: string; last_name?: string; date_of_birth?: string }) =>
      oisApi.lookupPatients(selectedConn!, params),
    onSuccess: (data) => {
      setPatients(data);
      if (data.length === 0) {
        notifications.show({ title: 'No Results', message: 'No patients found matching criteria', color: 'yellow' });
      }
    },
    onError: () => {
      notifications.show({ title: 'Lookup Failed', message: 'Could not search the OIS', color: 'red' });
    },
  });

  const importMutation = useMutation({
    mutationFn: (externalId: string) => oisApi.importPatient(selectedConn!, externalId),
    onSuccess: (result) => {
      notifications.show({
        title: result.success ? 'Patient Imported' : 'Import Failed',
        message: result.message,
        color: result.success ? 'green' : 'red',
      });
    },
  });

  const plansMutation = useMutation({
    mutationFn: (externalPatientId: string) => oisApi.getPatientPlans(selectedConn!, externalPatientId),
    onSuccess: (data, patientId) => {
      setPlans({ patientId, plans: data });
    },
  });

  const connOptions = connections.map((c) => ({
    value: c.id,
    label: `${c.name} (${c.ois_type.toUpperCase()})`,
  }));

  return (
    <Stack>
      <Card withBorder p="md">
        <Stack>
          <Select
            label="OIS Connection"
            placeholder="Select an OIS to search"
            data={connOptions}
            value={selectedConn}
            onChange={setSelectedConn}
          />

          {selectedConn && (
            <form
              onSubmit={form.onSubmit((values) => {
                const params: Record<string, string> = {};
                if (values.mrn) params.mrn = values.mrn;
                if (values.first_name) params.first_name = values.first_name;
                if (values.last_name) params.last_name = values.last_name;
                if (values.date_of_birth) params.date_of_birth = values.date_of_birth;
                lookupMutation.mutate(params);
              })}
            >
              <Group grow mb="md">
                <TextInput label="MRN" placeholder="Patient MRN" {...form.getInputProps('mrn')} />
                <TextInput label="Last Name" placeholder="Last name" {...form.getInputProps('last_name')} />
                <TextInput label="First Name" placeholder="First name" {...form.getInputProps('first_name')} />
                <TextInput label="Date of Birth" placeholder="YYYY-MM-DD" {...form.getInputProps('date_of_birth')} />
              </Group>
              <Button
                type="submit"
                leftSection={<RiSearchLine size={16} />}
                loading={lookupMutation.isPending}
              >
                Search OIS
              </Button>
            </form>
          )}
        </Stack>
      </Card>

      {patients.length > 0 && (
        <Card withBorder p="md">
          <Title order={5} mb="sm">Search Results</Title>
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>MRN</Table.Th>
                <Table.Th>Name</Table.Th>
                <Table.Th>DOB</Table.Th>
                <Table.Th>Sex</Table.Th>
                <Table.Th>Source</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {patients.map((p) => (
                <Table.Tr key={p.external_id}>
                  <Table.Td><Text fw={500}>{p.mrn}</Text></Table.Td>
                  <Table.Td>{p.last_name}, {p.first_name}{p.middle_name ? ` ${p.middle_name}` : ''}</Table.Td>
                  <Table.Td>{p.date_of_birth || 'N/A'}</Table.Td>
                  <Table.Td><Badge size="xs" variant="light">{p.sex || 'unknown'}</Badge></Table.Td>
                  <Table.Td><OISTypeBadge type={p.source_system} /></Table.Td>
                  <Table.Td>
                    <Group gap="xs">
                      <Tooltip label="Import Patient">
                        <ActionIcon
                          variant="light"
                          color="green"
                          loading={importMutation.isPending}
                          onClick={() => importMutation.mutate(p.external_id)}
                        >
                          <RiDownloadLine size={16} />
                        </ActionIcon>
                      </Tooltip>
                      <Tooltip label="View Plans">
                        <ActionIcon
                          variant="light"
                          color="blue"
                          loading={plansMutation.isPending}
                          onClick={() => plansMutation.mutate(p.external_id)}
                        >
                          <RiSearchLine size={16} />
                        </ActionIcon>
                      </Tooltip>
                    </Group>
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Card>
      )}

      {plans && (
        <Card withBorder p="md">
          <Title order={5} mb="sm">Treatment Plans (Patient: {plans.patientId})</Title>
          {plans.plans.length === 0 ? (
            <Text c="dimmed">No treatment plans found.</Text>
          ) : (
            <Table striped>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Plan Label</Table.Th>
                  <Table.Th>Modality</Table.Th>
                  <Table.Th>Technique</Table.Th>
                  <Table.Th>Beams</Table.Th>
                  <Table.Th>Dose (cGy)</Table.Th>
                  <Table.Th>Fractions</Table.Th>
                  <Table.Th>Status</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {plans.plans.map((plan) => (
                  <Table.Tr key={plan.external_id}>
                    <Table.Td><Text fw={500}>{plan.plan_label}</Text></Table.Td>
                    <Table.Td>{plan.modality || 'N/A'}</Table.Td>
                    <Table.Td>{plan.technique || 'N/A'}</Table.Td>
                    <Table.Td>{plan.num_beams}</Table.Td>
                    <Table.Td>{plan.prescribed_dose_cgy?.toFixed(0) || 'N/A'}</Table.Td>
                    <Table.Td>{plan.num_fractions || 'N/A'}</Table.Td>
                    <Table.Td>
                      <Badge
                        size="sm"
                        color={plan.approval_status === 'Approved' ? 'green' : 'yellow'}
                        variant="light"
                      >
                        {plan.approval_status || plan.status || 'Unknown'}
                      </Badge>
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          )}
        </Card>
      )}
    </Stack>
  );
}

// ── Schedule Sync Tab ────────────────────────────────────────────────

function ScheduleSyncTab() {
  const [selectedConn, setSelectedConn] = useState<string | null>(null);

  const { data: connections = [] } = useQuery({
    queryKey: ['ois-connections'],
    queryFn: () => oisApi.listConnections(true),
  });

  const form = useForm({
    initialValues: {
      date_from: new Date().toISOString().split('T')[0],
      date_to: new Date().toISOString().split('T')[0],
      machine_name: '',
    },
  });

  const syncMutation = useMutation({
    mutationFn: (data: { connection_id: string; date_from: string; date_to: string; machine_name?: string }) =>
      oisApi.syncSchedule(data),
    onSuccess: (result) => {
      notifications.show({
        title: result.success ? 'Sync Complete' : 'Sync Issues',
        message: `${result.appointments_synced} appointments synced (${result.appointments_created} new, ${result.appointments_updated} updated)${result.conflicts.length ? ` - ${result.conflicts.length} conflicts` : ''}`,
        color: result.success ? 'green' : 'yellow',
      });
    },
    onError: () => {
      notifications.show({ title: 'Sync Failed', message: 'Could not sync schedule', color: 'red' });
    },
  });

  const connOptions = connections.map((c) => ({
    value: c.id,
    label: `${c.name} (${c.ois_type.toUpperCase()})`,
  }));

  return (
    <Stack>
      <Card withBorder p="md">
        <form
          onSubmit={form.onSubmit((values) => {
            if (!selectedConn) return;
            syncMutation.mutate({
              connection_id: selectedConn,
              date_from: values.date_from ?? '',
              date_to: values.date_to ?? '',
              machine_name: values.machine_name || undefined,
            });
          })}
        >
          <Stack>
            <Select
              label="OIS Connection"
              placeholder="Select OIS"
              data={connOptions}
              value={selectedConn}
              onChange={setSelectedConn}
            />
            <Group grow>
              <TextInput label="From Date" placeholder="YYYY-MM-DD" {...form.getInputProps('date_from')} />
              <TextInput label="To Date" placeholder="YYYY-MM-DD" {...form.getInputProps('date_to')} />
              <TextInput label="Machine (optional)" placeholder="TrueBeam1" {...form.getInputProps('machine_name')} />
            </Group>
            <Button
              type="submit"
              leftSection={<RiRefreshLine size={16} />}
              loading={syncMutation.isPending}
              disabled={!selectedConn}
            >
              Sync Schedule
            </Button>
          </Stack>
        </form>
      </Card>

      {syncMutation.data && (
        <Card withBorder p="md">
          <SimpleGrid cols={3}>
            <Paper withBorder p="md" radius="md" ta="center">
              <Text size="xl" fw={700} c="blue">{syncMutation.data.appointments_synced}</Text>
              <Text size="sm" c="dimmed">Total Synced</Text>
            </Paper>
            <Paper withBorder p="md" radius="md" ta="center">
              <Text size="xl" fw={700} c="green">{syncMutation.data.appointments_created}</Text>
              <Text size="sm" c="dimmed">New</Text>
            </Paper>
            <Paper withBorder p="md" radius="md" ta="center">
              <Text size="xl" fw={700} c="orange">{syncMutation.data.conflicts.length}</Text>
              <Text size="sm" c="dimmed">Conflicts</Text>
            </Paper>
          </SimpleGrid>

          {syncMutation.data.conflicts.length > 0 && (
            <Alert color="yellow" mt="md" title="Sync Conflicts">
              <Stack gap="xs">
                {syncMutation.data.conflicts.map((c, i) => (
                  <Text key={i} size="sm">{c.external_id}: {c.reason}</Text>
                ))}
              </Stack>
            </Alert>
          )}
        </Card>
      )}
    </Stack>
  );
}

// ── Sync Logs Tab ────────────────────────────────────────────────────

function SyncLogsTab() {
  const { data: logs = [], isLoading } = useQuery({
    queryKey: ['ois-sync-logs'],
    queryFn: () => oisApi.getSyncLogs({ limit: 100 }),
    refetchInterval: 10000,
  });

  if (isLoading) return <Center py="xl"><Loader /></Center>;

  return (
    <Stack>
      <Text size="sm" c="dimmed">Recent synchronization activity across all OIS connections</Text>
      {logs.length === 0 ? (
        <Card withBorder p="xl">
          <Center>
            <Stack align="center" gap="xs">
              <ThemeIcon size={48} variant="light" color="gray" radius="xl"><RiHistoryLine size={24} /></ThemeIcon>
              <Text fw={500}>No Sync Activity</Text>
              <Text size="sm" c="dimmed">Sync logs will appear here once you start using OIS integrations.</Text>
            </Stack>
          </Center>
        </Card>
      ) : (
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>Time</Table.Th>
              <Table.Th>Operation</Table.Th>
              <Table.Th>Entity</Table.Th>
              <Table.Th>Status</Table.Th>
              <Table.Th>Records</Table.Th>
              <Table.Th>Duration</Table.Th>
              <Table.Th>Message</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {logs.map((log) => (
              <Table.Tr key={log.id}>
                <Table.Td>
                  <Text size="sm">{new Date(log.created_at).toLocaleString()}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge size="sm" variant="light">
                    {log.operation}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{log.entity_type || '-'}</Text>
                </Table.Td>
                <Table.Td>
                  <Badge
                    size="sm"
                    color={log.status === 'success' ? 'green' : log.status === 'partial' ? 'yellow' : 'red'}
                    variant="light"
                  >
                    {log.status}
                  </Badge>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">
                    {log.records_processed}
                    {log.records_failed > 0 && (
                      <Text span c="red" size="sm"> ({log.records_failed} failed)</Text>
                    )}
                  </Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm">{log.duration_ms ? `${log.duration_ms.toFixed(0)}ms` : '-'}</Text>
                </Table.Td>
                <Table.Td>
                  <Text size="sm" lineClamp={1}>{log.message || '-'}</Text>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      )}
    </Stack>
  );
}

// ── Main Page ────────────────────────────────────────────────────────

export default function OISIntegrationPage() {
  return (
    <Stack>
      <Group justify="space-between">
        <div>
          <Title order={2}>OIS Integration</Title>
          <Text c="dimmed">Connect to ARIA, RayCare, or FHIR systems for patient and plan synchronization</Text>
        </div>
      </Group>

      <Tabs defaultValue="connections">
        <Tabs.List>
          <Tabs.Tab value="connections" leftSection={<RiPlugLine size={16} />}>
            Connections
          </Tabs.Tab>
          <Tabs.Tab value="patients" leftSection={<RiUserSearchLine size={16} />}>
            Patient Lookup
          </Tabs.Tab>
          <Tabs.Tab value="schedule" leftSection={<RiCalendarLine size={16} />}>
            Schedule Sync
          </Tabs.Tab>
          <Tabs.Tab value="logs" leftSection={<RiHistoryLine size={16} />}>
            Sync Logs
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="connections" pt="md">
          <ConnectionsTab />
        </Tabs.Panel>

        <Tabs.Panel value="patients" pt="md">
          <PatientLookupTab />
        </Tabs.Panel>

        <Tabs.Panel value="schedule" pt="md">
          <ScheduleSyncTab />
        </Tabs.Panel>

        <Tabs.Panel value="logs" pt="md">
          <SyncLogsTab />
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
