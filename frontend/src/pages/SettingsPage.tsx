import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text,
  TextInput, NumberInput, Modal, Tabs, Switch, Loader, ActionIcon, Tooltip,
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconTrash, IconWifi, IconServer, IconSettings } from '@tabler/icons-react';
import { dicomApi } from '../api/dicom';

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [peerModalOpen, setPeerModalOpen] = useState(false);

  const { data: dicomStatus, isLoading: statusLoading } = useQuery({
    queryKey: ['dicom-status'],
    queryFn: () => dicomApi.getStatus(),
    refetchInterval: 5000,
  });

  const { data: peers = [], isLoading: peersLoading } = useQuery({
    queryKey: ['dicom-peers'],
    queryFn: () => dicomApi.listPeers(),
  });

  const peerForm = useForm({
    initialValues: {
      name: '',
      ae_title: '',
      host: '',
      port: 104,
      description: '',
    },
  });

  const startScpMutation = useMutation({
    mutationFn: () => dicomApi.startScp(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dicom-status'] });
      notifications.show({ title: 'Success', message: 'DICOM SCP started', color: 'green' });
    },
  });

  const stopScpMutation = useMutation({
    mutationFn: () => dicomApi.stopScp(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dicom-status'] });
      notifications.show({ title: 'Info', message: 'DICOM SCP stopped', color: 'blue' });
    },
  });

  const addPeerMutation = useMutation({
    mutationFn: (data: typeof peerForm.values) => dicomApi.addPeer(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dicom-peers'] });
      setPeerModalOpen(false);
      peerForm.reset();
      notifications.show({ title: 'Success', message: 'Peer added', color: 'green' });
    },
  });

  const removePeerMutation = useMutation({
    mutationFn: (name: string) => dicomApi.removePeer(name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dicom-peers'] });
      notifications.show({ title: 'Info', message: 'Peer removed', color: 'blue' });
    },
  });

  const echoPeerMutation = useMutation({
    mutationFn: (name: string) => dicomApi.echoPeer(name),
    onSuccess: (data) => {
      notifications.show({
        title: data.success ? 'Success' : 'Failed',
        message: data.success ? `C-ECHO to ${data.peer_name} successful` : `C-ECHO to ${data.peer_name} failed`,
        color: data.success ? 'green' : 'red',
      });
    },
  });

  return (
    <Stack>
      <Title order={2}>Settings</Title>

      <Tabs defaultValue="dicom">
        <Tabs.List>
          <Tabs.Tab value="dicom" leftSection={<IconServer size={16} />}>DICOM Configuration</Tabs.Tab>
          <Tabs.Tab value="general" leftSection={<IconSettings size={16} />}>General Settings</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="dicom" pt="md">
          <Stack>
            <Card withBorder>
              <Group justify="space-between">
                <div>
                  <Text fw={700}>DICOM SCP Server</Text>
                  <Text size="sm" c="dimmed">Storage Class Provider - receives DICOM objects from remote systems</Text>
                </div>
                <Group>
                  {statusLoading ? (
                    <Loader size="sm" />
                  ) : (
                    <>
                      <Badge size="lg" color={dicomStatus?.scp_running ? 'green' : 'gray'} variant="dot">
                        {dicomStatus?.scp_running ? 'Running' : 'Stopped'}
                      </Badge>
                      {dicomStatus?.scp_running ? (
                        <Button color="red" variant="light" onClick={() => stopScpMutation.mutate()} loading={stopScpMutation.isPending}>
                          Stop SCP
                        </Button>
                      ) : (
                        <Button color="green" onClick={() => startScpMutation.mutate()} loading={startScpMutation.isPending}>
                          Start SCP
                        </Button>
                      )}
                    </>
                  )}
                </Group>
              </Group>
              {dicomStatus?.scp_running && (
                <Group mt="md" gap="xl">
                  <div>
                    <Text size="xs" c="dimmed">AE Title</Text>
                    <Text style={{ fontFamily: 'monospace' }}>{dicomStatus.scp_ae_title}</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed">Port</Text>
                    <Text style={{ fontFamily: 'monospace' }}>{dicomStatus.scp_port}</Text>
                  </div>
                  <div>
                    <Text size="xs" c="dimmed">Registered Peers</Text>
                    <Text>{dicomStatus.registered_peers}</Text>
                  </div>
                </Group>
              )}
            </Card>

            <Card withBorder>
              <Group justify="space-between" mb="md">
                <div>
                  <Text fw={700}>DICOM Peers</Text>
                  <Text size="sm" c="dimmed">Remote DICOM systems (TPS, PACS, linac controllers)</Text>
                </div>
                <Button leftSection={<IconPlus size={16} />} variant="light" onClick={() => setPeerModalOpen(true)}>
                  Add Peer
                </Button>
              </Group>

              {peersLoading ? (
                <Group justify="center" py="xl"><Loader /></Group>
              ) : (
                <Table striped highlightOnHover>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>Name</Table.Th>
                      <Table.Th>AE Title</Table.Th>
                      <Table.Th>Host</Table.Th>
                      <Table.Th>Port</Table.Th>
                      <Table.Th>Description</Table.Th>
                      <Table.Th>Actions</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {peers.map((peer) => (
                      <Table.Tr key={peer.name}>
                        <Table.Td><Text fw={600}>{peer.name}</Text></Table.Td>
                        <Table.Td><Text style={{ fontFamily: 'monospace' }}>{peer.ae_title}</Text></Table.Td>
                        <Table.Td>{peer.host}</Table.Td>
                        <Table.Td>{peer.port}</Table.Td>
                        <Table.Td>{peer.description || '-'}</Table.Td>
                        <Table.Td>
                          <Group gap="xs">
                            <Tooltip label="Test Connection (C-ECHO)">
                              <ActionIcon variant="subtle" color="blue" onClick={() => echoPeerMutation.mutate(peer.name)}>
                                <IconWifi size={16} />
                              </ActionIcon>
                            </Tooltip>
                            <Tooltip label="Remove">
                              <ActionIcon variant="subtle" color="red" onClick={() => removePeerMutation.mutate(peer.name)}>
                                <IconTrash size={16} />
                              </ActionIcon>
                            </Tooltip>
                          </Group>
                        </Table.Td>
                      </Table.Tr>
                    ))}
                    {peers.length === 0 && (
                      <Table.Tr>
                        <Table.Td colSpan={6}>
                          <Text ta="center" c="dimmed" py="xl">
                            No DICOM peers configured. Add TPS, PACS, or linac connections.
                          </Text>
                        </Table.Td>
                      </Table.Tr>
                    )}
                  </Table.Tbody>
                </Table>
              )}
            </Card>
          </Stack>
        </Tabs.Panel>

        <Tabs.Panel value="general" pt="md">
          <Card withBorder p="lg">
            <Stack>
              <Text fw={700}>Application Settings</Text>
              <Group grow>
                <TextInput label="Institution Name" placeholder="Hospital/Clinic name" />
                <TextInput label="Department" placeholder="Radiation Oncology" />
              </Group>
              <Group grow>
                <NumberInput label="Session Timeout (minutes)" defaultValue={30} min={5} max={120} />
                <NumberInput label="Password Expiry (days)" defaultValue={90} min={30} max={365} />
              </Group>
              <Switch label="Require two-identifier patient verification" defaultChecked />
              <Switch label="Require electronic signature for plan approval" defaultChecked />
              <Switch label="Auto-lock account after 5 failed login attempts" defaultChecked />
              <Button variant="light" mt="sm">Save Settings</Button>
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      <Modal opened={peerModalOpen} onClose={() => setPeerModalOpen(false)} title="Add DICOM Peer">
        <form onSubmit={peerForm.onSubmit((values) => addPeerMutation.mutate(values))}>
          <Stack>
            <TextInput label="Name" placeholder="e.g. TPS-Eclipse" required {...peerForm.getInputProps('name')} />
            <TextInput label="AE Title" placeholder="e.g. ECLIPSE" required maxLength={16} {...peerForm.getInputProps('ae_title')} />
            <Group grow>
              <TextInput label="Host" placeholder="192.168.1.100" required {...peerForm.getInputProps('host')} />
              <NumberInput label="Port" min={1} max={65535} required {...peerForm.getInputProps('port')} />
            </Group>
            <TextInput label="Description" placeholder="Varian Eclipse TPS" {...peerForm.getInputProps('description')} />
            <Button type="submit" loading={addPeerMutation.isPending}>Add Peer</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
