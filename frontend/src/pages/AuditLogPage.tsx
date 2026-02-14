import { useState } from 'react';
import {
  Title, Card, Stack, Group, Table, Badge, Text, Select,
  Loader, Code, Spoiler, Pagination,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import api from '../api/client';

interface AuditLog {
  id: string;
  user_id: string | null;
  action: string;
  entity_type: string;
  entity_id: string;
  changed_fields: string[] | null;
  old_values: Record<string, unknown> | null;
  new_values: Record<string, unknown> | null;
  ip_address: string | null;
  request_id: string | null;
  created_at: string;
}

const ACTION_COLORS: Record<string, string> = {
  create: 'green',
  update: 'blue',
  delete: 'red',
  login: 'cyan',
  approve: 'grape',
  override: 'orange',
};

export default function AuditLogPage() {
  const [page, setPage] = useState(1);
  const [entityTypeFilter, setEntityTypeFilter] = useState<string | null>(null);
  const [actionFilter, setActionFilter] = useState<string | null>(null);
  const pageSize = 50;

  const { data, isLoading } = useQuery({
    queryKey: ['audit-logs', page, entityTypeFilter, actionFilter],
    queryFn: () => api.get<AuditLog[]>('/audit/logs', {
      params: {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...(entityTypeFilter ? { entity_type: entityTypeFilter } : {}),
        ...(actionFilter ? { action: actionFilter } : {}),
      },
    }).then(r => r.data),
  });

  const logs = data || [];

  return (
    <Stack>
      <Title order={2}>Audit Log</Title>

      <Group>
        <Select
          placeholder="Filter by entity"
          clearable
          value={entityTypeFilter}
          onChange={setEntityTypeFilter}
          data={[
            { value: 'user', label: 'User' },
            { value: 'patient', label: 'Patient' },
            { value: 'treatment_plan', label: 'Treatment Plan' },
            { value: 'treatment_session', label: 'Treatment Session' },
            { value: 'beam_delivery_record', label: 'Beam Delivery' },
            { value: 'prescription', label: 'Prescription' },
            { value: 'qa_record', label: 'QA Record' },
          ]}
        />
        <Select
          placeholder="Filter by action"
          clearable
          value={actionFilter}
          onChange={setActionFilter}
          data={[
            { value: 'create', label: 'Create' },
            { value: 'update', label: 'Update' },
            { value: 'delete', label: 'Delete' },
            { value: 'login', label: 'Login' },
            { value: 'approve', label: 'Approve' },
            { value: 'override', label: 'Override' },
          ]}
        />
      </Group>

      <Card withBorder>
        {isLoading ? (
          <Group justify="center" py="xl"><Loader /></Group>
        ) : (
          <>
            <Table striped highlightOnHover>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>Timestamp</Table.Th>
                  <Table.Th>Action</Table.Th>
                  <Table.Th>Entity</Table.Th>
                  <Table.Th>Changed Fields</Table.Th>
                  <Table.Th>IP Address</Table.Th>
                  <Table.Th>Details</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {logs.map((log) => (
                  <Table.Tr key={log.id}>
                    <Table.Td><Text size="sm">{new Date(log.created_at).toLocaleString()}</Text></Table.Td>
                    <Table.Td>
                      <Badge color={ACTION_COLORS[log.action] || 'gray'} size="sm">{log.action}</Badge>
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm">{log.entity_type}</Text>
                      <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>{log.entity_id.substring(0, 8)}...</Text>
                    </Table.Td>
                    <Table.Td>
                      {log.changed_fields?.map((field) => (
                        <Badge key={field} size="xs" variant="outline" mr={2}>{field}</Badge>
                      )) || '-'}
                    </Table.Td>
                    <Table.Td>
                      <Text size="sm" style={{ fontFamily: 'monospace' }}>{log.ip_address || '-'}</Text>
                    </Table.Td>
                    <Table.Td>
                      {(log.old_values || log.new_values) && (
                        <Spoiler maxHeight={0} showLabel="Show" hideLabel="Hide">
                          {log.old_values && (
                            <div>
                              <Text size="xs" fw={600}>Before:</Text>
                              <Code block>{JSON.stringify(log.old_values, null, 2)}</Code>
                            </div>
                          )}
                          {log.new_values && (
                            <div>
                              <Text size="xs" fw={600}>After:</Text>
                              <Code block>{JSON.stringify(log.new_values, null, 2)}</Code>
                            </div>
                          )}
                        </Spoiler>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
                {logs.length === 0 && (
                  <Table.Tr>
                    <Table.Td colSpan={6}>
                      <Text ta="center" c="dimmed" py="xl">
                        No audit log entries. All data changes are permanently recorded for 21 CFR Part 11 compliance.
                      </Text>
                    </Table.Td>
                  </Table.Tr>
                )}
              </Table.Tbody>
            </Table>
            <Group justify="center" mt="md">
              <Pagination total={10} value={page} onChange={setPage} />
            </Group>
          </>
        )}
      </Card>
    </Stack>
  );
}
