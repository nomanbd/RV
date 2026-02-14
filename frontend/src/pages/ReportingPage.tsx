import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Text,
  SimpleGrid, RingProgress, Tabs, Loader, TextInput, Paper,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconChartBar, IconFileReport, IconActivity, IconDownload, IconPrinter } from '@tabler/icons-react';
import { reportingApi } from '../api/reporting';
import { useAppStore } from '../store';

function generateCSV(headers: string[], rows: string[][]): string {
  const escape = (v: string) => `"${v.replace(/"/g, '""')}"`;
  const headerLine = headers.map(escape).join(',');
  const dataLines = rows.map((row) => row.map(escape).join(','));
  return [headerLine, ...dataLines].join('\n');
}

function downloadFile(content: string, filename: string, type = 'text/csv') {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ReportingPage() {
  const { selectedPatient } = useAppStore();
  const [reportPatientId, setReportPatientId] = useState<string>(selectedPatient?.id || '');

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dashboard-stats'],
    queryFn: () => reportingApi.getDashboardStats(),
    retry: false,
  });

  const { data: utilization = [], isLoading: utilizationLoading } = useQuery({
    queryKey: ['machine-utilization'],
    queryFn: () => reportingApi.getMachineUtilization(),
    retry: false,
  });

  const { data: treatmentSummary, isLoading: summaryLoading } = useQuery({
    queryKey: ['treatment-summary', reportPatientId],
    queryFn: () => reportingApi.getTreatmentSummary(reportPatientId),
    enabled: !!reportPatientId,
    retry: false,
  });

  const handleExportTreatmentSummary = () => {
    if (!treatmentSummary) {
      notifications.show({ title: 'No Data', message: 'Load a patient treatment summary first', color: 'yellow' });
      return;
    }
    const headers = ['Course', 'Intent', 'Site', 'Modality', 'Technique', 'Dose (Gy)', 'Fractions', 'Delivered (Gy)', 'Status'];
    const rows: string[][] = [];
    treatmentSummary.courses.forEach((course) => {
      course.prescriptions.forEach((rx) => {
        rows.push([
          `Course ${course.course_number}`,
          course.intent,
          rx.site_name,
          rx.modality,
          rx.technique,
          (rx.total_dose_cgy / 100).toFixed(1),
          rx.num_fractions.toString(),
          (course.total_delivered_dose_cgy / 100).toFixed(1),
          `${course.fractions_completed}/${course.fractions_total} fx`,
        ]);
      });
    });
    const csv = generateCSV(headers, rows);
    downloadFile(csv, `treatment_summary_${treatmentSummary.mrn}_${new Date().toISOString().split('T')[0]}.csv`);
    notifications.show({ title: 'Report Exported', message: 'Treatment summary CSV downloaded', color: 'green' });
  };

  const handleExportMachineUtilization = () => {
    if (utilization.length === 0) {
      notifications.show({ title: 'No Data', message: 'No utilization data available', color: 'yellow' });
      return;
    }
    const headers = ['Machine', 'Total Sessions', 'Completed', 'Beam-On Minutes', 'Utilization %', 'From', 'To'];
    const rows = utilization.map((m) => [
      m.machine_name, m.total_sessions.toString(), m.completed_sessions.toString(),
      m.total_beam_on_minutes.toFixed(0), m.utilization_percentage.toFixed(1),
      m.date_from, m.date_to,
    ]);
    const csv = generateCSV(headers, rows);
    downloadFile(csv, `machine_utilization_${new Date().toISOString().split('T')[0]}.csv`);
    notifications.show({ title: 'Report Exported', message: 'Machine utilization CSV downloaded', color: 'green' });
  };

  const handlePrintReport = () => {
    window.print();
  };

  return (
    <Stack>
      <Title order={2}>Reports & Analytics</Title>

      <Tabs defaultValue="dashboard">
        <Tabs.List>
          <Tabs.Tab value="dashboard" leftSection={<IconChartBar size={16} />}>Dashboard</Tabs.Tab>
          <Tabs.Tab value="utilization" leftSection={<IconActivity size={16} />}>Machine Utilization</Tabs.Tab>
          <Tabs.Tab value="reports" leftSection={<IconFileReport size={16} />}>Generate Reports</Tabs.Tab>
        </Tabs.List>

        <Tabs.Panel value="dashboard" pt="md">
          {statsLoading ? (
            <Group justify="center" py="xl"><Loader /></Group>
          ) : stats ? (
            <SimpleGrid cols={{ base: 2, md: 4 }}>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Total Patients</Text>
                <Text size="xl" fw={700}>{stats.total_patients}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Active Plans</Text>
                <Text size="xl" fw={700}>{stats.active_plans}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Today's Appointments</Text>
                <Text size="xl" fw={700}>{stats.todays_appointments}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Pending Tasks</Text>
                <Text size="xl" fw={700}>{stats.pending_tasks}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>Machines Active</Text>
                <Text size="xl" fw={700}>{stats.machines_active} / {stats.machines_total}</Text>
              </Card>
              <Card withBorder p="md">
                <Text size="xs" c="dimmed" tt="uppercase" fw={700}>QA Due</Text>
                <Text size="xl" fw={700} c={stats.qa_due > 0 ? 'orange' : undefined}>{stats.qa_due}</Text>
              </Card>
            </SimpleGrid>
          ) : (
            <Text c="dimmed" ta="center">No data available</Text>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="utilization" pt="md">
          <Group justify="flex-end" mb="md">
            <Button variant="light" leftSection={<IconDownload size={16} />} onClick={handleExportMachineUtilization}>
              Export CSV
            </Button>
          </Group>
          {utilizationLoading ? (
            <Group justify="center" py="xl"><Loader /></Group>
          ) : (
            <SimpleGrid cols={{ base: 1, md: 2, lg: 3 }}>
              {utilization.map((machine) => (
                <Card key={machine.machine_id} withBorder p="lg">
                  <Group justify="space-between" mb="md">
                    <div>
                      <Text fw={700}>{machine.machine_name}</Text>
                      <Text size="sm" c="dimmed">{machine.completed_sessions} / {machine.total_sessions} sessions</Text>
                    </div>
                    <RingProgress
                      size={80} thickness={8} roundCaps
                      sections={[{ value: machine.utilization_percentage, color: machine.utilization_percentage > 80 ? 'green' : 'blue' }]}
                      label={<Text ta="center" size="xs" fw={700}>{machine.utilization_percentage.toFixed(0)}%</Text>}
                    />
                  </Group>
                  <Text size="sm">Total beam-on time: {machine.total_beam_on_minutes.toFixed(0)} min</Text>
                </Card>
              ))}
              {utilization.length === 0 && (
                <Card withBorder p="xl"><Text ta="center" c="dimmed">No utilization data available</Text></Card>
              )}
            </SimpleGrid>
          )}
        </Tabs.Panel>

        <Tabs.Panel value="reports" pt="md">
          <SimpleGrid cols={{ base: 1, md: 2 }}>
            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Treatment Summary Report</Text>
                <Text size="sm" c="dimmed">Complete treatment summary including prescriptions, plans, fractions delivered, and cumulative dose.</Text>
                <TextInput
                  label="Patient ID"
                  placeholder="Enter patient ID or select patient first"
                  value={reportPatientId}
                  onChange={(e) => setReportPatientId(e.currentTarget.value)}
                  size="sm"
                />
                {treatmentSummary && (
                  <Paper p="sm" bg="gray.0" radius="sm">
                    <Text size="sm" fw={600}>{treatmentSummary.patient_name} (MRN: {treatmentSummary.mrn})</Text>
                    <Text size="xs" c="dimmed">{treatmentSummary.courses.length} courses | Generated: {new Date(treatmentSummary.generated_at).toLocaleString()}</Text>
                  </Paper>
                )}
                <Group>
                  <Button variant="light" leftSection={<IconDownload size={16} />} onClick={handleExportTreatmentSummary} loading={summaryLoading}>
                    Export CSV
                  </Button>
                  <Button variant="subtle" leftSection={<IconPrinter size={16} />} onClick={handlePrintReport}>
                    Print
                  </Button>
                </Group>
              </Stack>
            </Card>

            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Machine Utilization Report</Text>
                <Text size="sm" c="dimmed">Machine usage statistics, session counts, and beam-on time metrics.</Text>
                <Button variant="light" leftSection={<IconDownload size={16} />} onClick={handleExportMachineUtilization}>
                  Export CSV
                </Button>
              </Stack>
            </Card>

            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Machine QA Report</Text>
                <Text size="sm" c="dimmed">Summary of QA checks, pass/fail rates, and compliance metrics for each machine.</Text>
                <Button variant="light" leftSection={<IconPrinter size={16} />} onClick={handlePrintReport}>
                  Print Report
                </Button>
              </Stack>
            </Card>

            <Card withBorder p="lg">
              <Stack>
                <Text fw={700}>Compliance Report</Text>
                <Text size="sm" c="dimmed">21 CFR Part 11 compliance summary including electronic signatures and audit trail statistics.</Text>
                <Button variant="light" leftSection={<IconPrinter size={16} />} onClick={handlePrintReport}>
                  Print Report
                </Button>
              </Stack>
            </Card>
          </SimpleGrid>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
