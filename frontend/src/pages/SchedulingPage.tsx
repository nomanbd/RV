import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text, Modal,
  TextInput, Select, Tabs, Loader,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { useForm } from '@mantine/form';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconPlus, IconCalendar, IconList, IconBell } from '@tabler/icons-react';
import { schedulingApi } from '../api/scheduling';

const APPT_STATUS_COLORS: Record<string, string> = {
  scheduled: 'blue',
  checked_in: 'cyan',
  in_progress: 'yellow',
  completed: 'green',
  cancelled: 'red',
  no_show: 'orange',
};

const TASK_STATUS_COLORS: Record<string, string> = {
  pending: 'gray',
  in_progress: 'blue',
  completed: 'green',
  blocked: 'red',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'gray',
  medium: 'blue',
  high: 'orange',
  urgent: 'red',
};

export default function SchedulingPage() {
  const queryClient = useQueryClient();
  const [appointmentModalOpen, setAppointmentModalOpen] = useState(false);

  const { data: appointments = [], isLoading: apptLoading } = useQuery({
    queryKey: ['appointments'],
    queryFn: () => schedulingApi.listAppointments(),
  });

  const { data: tasks = [], isLoading: tasksLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => schedulingApi.listTasks(),
  });

  const { data: appNotifications = [] } = useQuery({
    queryKey: ['notifications'],
    queryFn: () => schedulingApi.getNotifications(),
  });

  const appointmentForm = useForm({
    initialValues: {
      patient_id: '',
      appointment_type: 'treatment',
      scheduled_start: new Date(),
      scheduled_end: new Date(Date.now() + 30 * 60 * 1000),
      notes: '',
    },
  });

  const createAppointmentMutation = useMutation({
    mutationFn: (data: typeof appointmentForm.values) =>
      schedulingApi.createAppointment({
        ...data,
        scheduled_start: data.scheduled_start.toISOString(),
        scheduled_end: data.scheduled_end.toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['appointments'] });
      setAppointmentModalOpen(false);
      appointmentForm.reset();
      notifications.show({ title: 'Success', message: 'Appointment created', color: 'green' });
    },
  });

  const markReadMutation = useMutation({
    mutationFn: (notificationId: string) => schedulingApi.markNotificationRead(notificationId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['notifications'] }),
  });

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Scheduling & Workflow</Title>
        <Button leftSection={<IconPlus size={16} />} onClick={() => setAppointmentModalOpen(true)}>
          New Appointment
        </Button>
      </Group>

      <Tabs defaultValue="appointments">
        <Tabs.List>
          <Tabs.Tab value="appointments" leftSection={<IconCalendar size={16} />}>Appointments</Tabs.Tab>
          <Tabs.Tab value="tasks" leftSection={<IconList size={16} />}>Workflow Tasks</Tabs.Tab>
          <Tabs.Tab value="notifications" leftSection={<IconBell size={16} />} rightSection={
            appNotifications.length > 0 ? <Badge size="xs" color="red">{appNotifications.length}</Badge> : null
          }>
            Notifications
          </Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="appointments" pt="md">
          <Card withBorder>
            {apptLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Scheduled</Table.Th>
                    <Table.Th>Duration</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Notes</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {appointments.map((appt) => (
                    <Table.Tr key={appt.id}>
                      <Table.Td><Badge variant="light">{appt.appointment_type}</Badge></Table.Td>
                      <Table.Td>{new Date(appt.scheduled_start).toLocaleString()}</Table.Td>
                      <Table.Td>
                        {Math.round((new Date(appt.scheduled_end).getTime() - new Date(appt.scheduled_start).getTime()) / 60000)} min
                      </Table.Td>
                      <Table.Td>
                        <Badge color={APPT_STATUS_COLORS[appt.status] || 'gray'}>{appt.status.replace(/_/g, ' ')}</Badge>
                      </Table.Td>
                      <Table.Td>{appt.notes || '-'}</Table.Td>
                    </Table.Tr>
                  ))}
                  {appointments.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text ta="center" c="dimmed" py="xl">No appointments scheduled</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="tasks" pt="md">
          <Card withBorder>
            {tasksLoading ? (
              <Group justify="center" py="xl"><Loader /></Group>
            ) : (
              <Table striped highlightOnHover>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Task</Table.Th>
                    <Table.Th>Type</Table.Th>
                    <Table.Th>Priority</Table.Th>
                    <Table.Th>Status</Table.Th>
                    <Table.Th>Due</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {tasks.map((task) => (
                    <Table.Tr key={task.id}>
                      <Table.Td>
                        <Text fw={600}>{task.title}</Text>
                        {task.description && <Text size="xs" c="dimmed">{task.description}</Text>}
                      </Table.Td>
                      <Table.Td><Badge variant="outline">{task.task_type}</Badge></Table.Td>
                      <Table.Td>
                        <Badge color={PRIORITY_COLORS[task.priority] || 'gray'} size="sm">{task.priority}</Badge>
                      </Table.Td>
                      <Table.Td>
                        <Badge color={TASK_STATUS_COLORS[task.status] || 'gray'}>{task.status.replace(/_/g, ' ')}</Badge>
                      </Table.Td>
                      <Table.Td>{task.due_date ? new Date(task.due_date).toLocaleDateString() : '-'}</Table.Td>
                    </Table.Tr>
                  ))}
                  {tasks.length === 0 && (
                    <Table.Tr>
                      <Table.Td colSpan={5}>
                        <Text ta="center" c="dimmed" py="xl">No workflow tasks</Text>
                      </Table.Td>
                    </Table.Tr>
                  )}
                </Table.Tbody>
              </Table>
            )}
          </Card>
        </Tabs.Panel>

        <Tabs.Panel value="notifications" pt="md">
          <Card withBorder>
            <Stack>
              {appNotifications.length === 0 ? (
                <Text ta="center" c="dimmed" py="xl">No unread notifications</Text>
              ) : (
                appNotifications.map((notif) => (
                  <Card key={notif.id} withBorder p="sm">
                    <Group justify="space-between">
                      <div>
                        <Text fw={600}>{notif.title}</Text>
                        <Text size="sm" c="dimmed">{notif.message}</Text>
                        <Text size="xs" c="dimmed">{new Date(notif.created_at).toLocaleString()}</Text>
                      </div>
                      <Button size="xs" variant="subtle" onClick={() => markReadMutation.mutate(notif.id)}>
                        Mark Read
                      </Button>
                    </Group>
                  </Card>
                ))
              )}
            </Stack>
          </Card>
        </Tabs.Panel>
      </Tabs>

      <Modal opened={appointmentModalOpen} onClose={() => setAppointmentModalOpen(false)} title="New Appointment">
        <form onSubmit={appointmentForm.onSubmit((v) => createAppointmentMutation.mutate(v))}>
          <Stack>
            <TextInput label="Patient ID" required {...appointmentForm.getInputProps('patient_id')} />
            <Select
              label="Type"
              data={[
                { value: 'treatment', label: 'Treatment' },
                { value: 'simulation', label: 'Simulation' },
                { value: 'consultation', label: 'Consultation' },
                { value: 'follow_up', label: 'Follow-up' },
              ]}
              {...appointmentForm.getInputProps('appointment_type')}
            />
            <DateTimePicker label="Start" {...appointmentForm.getInputProps('scheduled_start')} />
            <DateTimePicker label="End" {...appointmentForm.getInputProps('scheduled_end')} />
            <TextInput label="Notes" {...appointmentForm.getInputProps('notes')} />
            <Button type="submit" loading={createAppointmentMutation.isPending}>Create</Button>
          </Stack>
        </form>
      </Modal>
    </Stack>
  );
}
