import { useState, useCallback } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text, Modal,
  FileInput, Tabs, ActionIcon, Tooltip, Loader, Alert,
} from '@mantine/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconUpload, IconEye, IconCheck, IconSend } from '@tabler/icons-react';
import { planningApi } from '../api/planning';
import type { TreatmentPlan } from '../types/planning';
import ElectronicSignature from '../components/common/ElectronicSignature';

const STATUS_COLORS: Record<string, string> = {
  draft: 'gray',
  pending_review: 'yellow',
  reviewed: 'blue',
  approved: 'green',
};

export default function PlanManagementPage() {
  const queryClient = useQueryClient();
  const [selectedPlan, setSelectedPlan] = useState<TreatmentPlan | null>(null);
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [signatureModalOpen, setSignatureModalOpen] = useState(false);
  const [signatureAction, setSignatureAction] = useState<string>('');
  const [importFile, setImportFile] = useState<File | null>(null);

  const { data: plans = [], isLoading } = useQuery({
    queryKey: ['plans'],
    queryFn: () => planningApi.listPlans(),
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => planningApi.importPlan(file, '', ''),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      setImportModalOpen(false);
      notifications.show({ title: 'Success', message: 'Plan imported successfully', color: 'green' });
    },
    onError: () => {
      notifications.show({ title: 'Error', message: 'Failed to import plan', color: 'red' });
    },
  });

  const submitForReviewMutation = useMutation({
    mutationFn: (planId: string) => planningApi.submitForReview(planId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      notifications.show({ title: 'Success', message: 'Plan submitted for review', color: 'green' });
    },
  });

  const handleSignatureComplete = useCallback(async (signatureId: string) => {
    if (!selectedPlan) return;
    try {
      if (signatureAction === 'review') {
        await planningApi.reviewPlan(selectedPlan.id, signatureId);
      } else if (signatureAction === 'approve') {
        await planningApi.approvePlan(selectedPlan.id, signatureId);
      } else if (signatureAction === 'physics_approve') {
        await planningApi.physicsApprovePlan(selectedPlan.id, signatureId);
      }
      queryClient.invalidateQueries({ queryKey: ['plans'] });
      notifications.show({ title: 'Success', message: `Plan ${signatureAction} completed`, color: 'green' });
    } catch {
      notifications.show({ title: 'Error', message: `Failed to ${signatureAction} plan`, color: 'red' });
    }
    setSignatureModalOpen(false);
  }, [selectedPlan, signatureAction, queryClient]);

  const openSignature = (plan: TreatmentPlan, action: string) => {
    setSelectedPlan(plan);
    setSignatureAction(action);
    setSignatureModalOpen(true);
  };

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Treatment Plans</Title>
        <Button leftSection={<IconUpload size={16} />} onClick={() => setImportModalOpen(true)}>
          Import DICOM Plan
        </Button>
      </Group>

      <Tabs defaultValue="all">
        <Tabs.List>
          <Tabs.Tab value="all">All Plans</Tabs.Tab>
          <Tabs.Tab value="draft">Draft</Tabs.Tab>
          <Tabs.Tab value="pending_review">Pending Review</Tabs.Tab>
          <Tabs.Tab value="approved">Approved</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="all" pt="md">
          <Card withBorder>
            {isLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Plan Label</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Version</Table.Th>
                    <Table.Th>Beams</Table.Th>
                    <Table.Th>Fractions</Table.Th>
                    <Table.Th>Created</Table.Th>
                    <Table.Th>Actions</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {plans.map((plan) => (
                    <Table.Tr key={plan.id}>
                      <Table.Td>
                        <Text fw={600}>{plan.plan_label}</Text>
                        {plan.plan_name && <Text size="xs" c="dimmed">{plan.plan_name}</Text>}
                      </Table.Td>
                      <Table.Td>
                        <Badge color={STATUS_COLORS[plan.status] || 'gray'}>
                          {plan.status.replace(/_/g, ' ')}
                        </Badge>
                      </Table.Td>
                      <Table.Td>v{plan.version}</Table.Td>
                      <Table.Td>{plan.num_beams ?? '-'}</Table.Td>
                      <Table.Td>{plan.num_fractions_planned ?? '-'}</Table.Td>
                      <Table.Td>{new Date(plan.created_at).toLocaleDateString()}</Table.Td>
                      <Table.Td>
                        <Group gap="xs">
                          <Tooltip label="View Details">
                            <ActionIcon variant="subtle" onClick={() => setSelectedPlan(plan)}>
                              <IconEye size={16} />
                            </ActionIcon>
                          </Tooltip>
                          {plan.status === 'draft' && (
                            <Tooltip label="Submit for Review">
                              <ActionIcon variant="subtle" color="blue" onClick={() => submitForReviewMutation.mutate(plan.id)}>
                                <IconSend size={16} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                          {plan.status === 'pending_review' && (
                            <Tooltip label="Review">
                              <ActionIcon variant="subtle" color="blue" onClick={() => openSignature(plan, 'review')}>
                                <IconCheck size={16} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                          {plan.status === 'reviewed' && (
                            <Tooltip label="Approve">
                              <ActionIcon variant="subtle" color="green" onClick={() => openSignature(plan, 'approve')}>
                                <IconCheck size={16} />
                              </ActionIcon>
                            </Tooltip>
                          )}
                        </Group>
                      </Table.Td>
                    </Table.Tr>
                  ))}
                  {plans.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={7}>
                        <Text ta="center" c="dimmed" py="xl">No treatment plans found. Import a DICOM RT Plan to get started.</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="draft" pt="md">
          <Card withBorder p="xl">
            <Text c="dimmed" ta="center">Draft plans will appear here</Text>
          </Card>
        </Tabs.Panel>
        <Tabs.Panel value="pending_review" pt="md">
          <Card withBorder p="xl">
            <Text c="dimmed" ta="center">Plans pending review will appear here</Text>
          </Card>
        </Tabs.Panel>
        <Tabs.Panel value="approved" pt="md">
          <Card withBorder p="xl">
            <Text c="dimmed" ta="center">Approved plans will appear here</Text>
          </Card>
        </Tabs.Panel>
      </Tabs>

      {/* Plan Detail Modal */}
      <Modal opened={!!selectedPlan && !signatureModalOpen} onClose={() => setSelectedPlan(null)} title="Plan Details" size="xl">
        {selectedPlan && (
          <Stack>
            <Group>
              <Text fw={600}>Plan:</Text>
              <Text>{selectedPlan.plan_label}</Text>
              <Badge color={STATUS_COLORS[selectedPlan.status] || 'gray'}>
                {selectedPlan.status.replace(/_/g, ' ')}
              </Badge>
            </Group>
            {selectedPlan.sop_instance_uid && (
              <Group>
                <Text fw={600}>SOP Instance UID:</Text>
                <Text size="sm" style={{ fontFamily: 'monospace' }}>{selectedPlan.sop_instance_uid}</Text>
              </Group>
            )}
            {selectedPlan.beams && selectedPlan.beams.length > 0 && (
              <>
                <Title order={4}>Beams ({selectedPlan.beams.length})</Title>
                <Table striped>
                  <Table.Thead>
                    <Table.Tr>
                      <Table.Th>#</Table.Th>
                      <Table.Th>Name</Table.Th>
                      <Table.Th>Type</Table.Th>
                      <Table.Th>Energy</Table.Th>
                      <Table.Th>Gantry</Table.Th>
                      <Table.Th>MU</Table.Th>
                    </Table.Tr>
                  </Table.Thead>
                  <Table.Tbody>
                    {selectedPlan.beams.map((beam) => (
                      <Table.Tr key={beam.id}>
                        <Table.Td>{beam.beam_number}</Table.Td>
                        <Table.Td>{beam.beam_name || '-'}</Table.Td>
                        <Table.Td>{beam.radiation_type}</Table.Td>
                        <Table.Td>{beam.energy_label || (beam.energy_mev ? `${beam.energy_mev} MeV` : '-')}</Table.Td>
                        <Table.Td>{beam.gantry_angle != null ? `${beam.gantry_angle}°` : '-'}</Table.Td>
                        <Table.Td>{beam.planned_mu != null ? beam.planned_mu.toFixed(1) : '-'}</Table.Td>
                      </Table.Tr>
                    ))}
                  </Table.Tbody>
                </Table>
              </>
            )}
            {selectedPlan.approved_at && (
              <Alert color="green" title="Plan Approved">
                Approved on {new Date(selectedPlan.approved_at).toLocaleString()}
              </Alert>
            )}
          </Stack>
        )}
      </Modal>

      {/* Import Modal */}
      <Modal opened={importModalOpen} onClose={() => setImportModalOpen(false)} title="Import DICOM RT Plan">
        <Stack>
          <FileInput
            label="DICOM RT Plan File"
            placeholder="Select .dcm file"
            accept=".dcm"
            value={importFile}
            onChange={setImportFile}
          />
          <Button
            onClick={() => importFile && importMutation.mutate(importFile)}
            loading={importMutation.isPending}
            disabled={!importFile}
          >
            Import Plan
          </Button>
        </Stack>
      </Modal>

      {/* Electronic Signature Modal */}
      <ElectronicSignature
        opened={signatureModalOpen}
        onClose={() => setSignatureModalOpen(false)}
        onComplete={handleSignatureComplete}
        meaning={signatureAction === 'review' ? 'review' : 'approval'}
        entityType="treatment_plan"
        entityId={selectedPlan?.id || ''}
      />
    </Stack>
  );
}
