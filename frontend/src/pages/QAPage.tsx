import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text,
  Tabs, Loader, ThemeIcon,
} from '@mantine/core';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconCheck, IconX, IconClipboardList, IconHistory } from '@tabler/icons-react';
import { qaApi } from '../api/qa';
import ElectronicSignature from '../components/common/ElectronicSignature';

export default function QAPage() {
  const queryClient = useQueryClient();
  const [signatureOpen, setSignatureOpen] = useState(false);
  const [selectedRecordId, setSelectedRecordId] = useState<string>('');

  const { data: checklists = [], isLoading: checklistsLoading } = useQuery({
    queryKey: ['qa-checklists'],
    queryFn: () => qaApi.listChecklists(),
  });

  const { data: records = [], isLoading: recordsLoading } = useQuery({
    queryKey: ['qa-records'],
    queryFn: () => qaApi.listRecords(),
  });

  const handleReview = (recordId: string) => {
    setSelectedRecordId(recordId);
    setSignatureOpen(true);
  };

  const handleSignatureComplete = async (signatureId: string) => {
    try {
      await qaApi.reviewRecord(selectedRecordId, signatureId);
      queryClient.invalidateQueries({ queryKey: ['qa-records'] });
      notifications.show({ title: 'Success', message: 'QA record reviewed', color: 'green' });
    } catch {
      notifications.show({ title: 'Error', message: 'Failed to review record', color: 'red' });
    }
    setSignatureOpen(false);
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Quality Assurance</Title>
        <Button leftSection={<IconPlus size={16} />}>New QA Checklist</Button>
      </Group>

      <Tabs defaultValue="checklists">
        <Tabs.List>
          <Tabs.Tab value="checklists" leftSection={<IconClipboardList size={16} />}>Checklists</Tabs.Tab>
          <Tabs.Tab value="records" leftSection={<IconHistory size={16} />}>QA Records</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="checklists" pt="md">
          <Card withBorder>
            {checklistsLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Name</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Items</Table.Th>
                    <Table.Th>Version</Table.Th>
                    <Table.Th>Status</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {checklists.map((checklist) => (
                    <Table.Tr key={checklist.id}>
                      <Table.Td><Text fw={600}>{checklist.name}</Text></Table.Td>
                      <Table.Td><Badge variant="outline">{checklist.checklist_type.replace(/_/g, ' ')}</Badge></Table.Td>
                      <Table.Td>{checklist.items.length}</Table.Td>
                      <Table.Td>v{checklist.version}</Table.Td>
                      <Table.Td>
                        <Badge color={checklist.is_active ? 'green' : 'gray'}>
                          {checklist.is_active ? 'Active' : 'Inactive'}
                        </Badge>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {checklists.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text ta="center" c="dimmed" py="xl">No QA checklists configured</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="records" pt="md">
          <Card withBorder>
            {recordsLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Date</Table.Th>
                    <Table.Th>Result</Table.Th>
                    <Table.Th>Notes</Table.Th>
                    <Table.Th>Reviewed</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {records.map((record) => (
                    <Table.Tr key={record.id}>
                      <Table.Td>{new Date(record.performed_at).toLocaleString()}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <ThemeIcon size="sm" variant="light" color={record.overall_pass ? 'green' : 'red'}>
                            {record.overall_pass ? <IconCheck size={14} /> : <IconX size={14} />}
                          </ThemeIcon>
                          <Text>{record.overall_pass ? 'Pass' : 'Fail'}</Text>
                        </Group>
                      </Table.Td>
                      <Table.Td>{record.notes || '-'}</Table.Td>
                      <Table.Td>
                        {record.reviewed_by_id ? (
                          <Badge color="green">Reviewed</Badge>
                        ) : (
                          <Badge color="yellow">Pending</Badge>
                        )}
                      </Table.Td>
                      <Table.Td>
                        {!record.reviewed_by_id && (
                          <Button size="xs" variant="light" onClick={() => handleReview(record.id)}>Review</Button>
                        )}
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {records.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text ta="center" c="dimmed" py="xl">No QA records found</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>
      </Tabs>

      <ElectronicSignature
        opened={signatureOpen}
        onClose={() => setSignatureOpen(false)}
        onSigned={(sig) => handleSignatureComplete(sig.id)}
        requiredMeaning="review"
        entityType="qa_record"
        entityId={selectedRecordId}
      />
    </Stack>
  );
}
