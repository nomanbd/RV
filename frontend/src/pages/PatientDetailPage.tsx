import { useParams } from 'react-router-dom';
import {
  Title, Tabs, Card, Stack, Text, Group, Badge, Table, Loader, Center,
  Timeline, ThemeIcon, Paper, Progress, Divider,
} from '@mantine/core';
import { useQuery } from '@tanstack/react-query';
import {
  RiUserLine, RiFileList3Line, RiPulseLine, RiImage2Line, RiTimeLine,
  RiCheckLine, RiCalendarLine, RiShieldCheckLine,
} from 'react-icons/ri';
import { patientsApi } from '../api/patients';
import { planningApi } from '../api/planning';
import { treatmentApi } from '../api/treatment';
import { imagingApi } from '../api/imaging';
import PatientBanner from '../components/common/PatientBanner';
import { useAppStore } from '../store';

const planStatusColor: Record<string, string> = {
  draft: 'gray', pending_review: 'yellow', reviewed: 'blue', approved: 'green',
};

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { setSelectedPatient } = useAppStore();

  const { data: patient, isLoading } = useQuery({
    queryKey: ['patient', id],
    queryFn: () => patientsApi.get(id!),
    enabled: !!id,
  });

  const { data: courses = [] } = useQuery({
    queryKey: ['patient-courses', id],
    queryFn: () => planningApi.listCourses({ patient_id: id }),
    enabled: !!id,
    retry: false,
  });

  const { data: plans = [] } = useQuery({
    queryKey: ['patient-plans', id],
    queryFn: () => planningApi.listPlans({ patient_id: id }),
    enabled: !!id,
    retry: false,
  });

  const { data: doseSummary } = useQuery({
    queryKey: ['patient-dose', id],
    queryFn: () => treatmentApi.getDoseSummary(id!),
    enabled: !!id,
    retry: false,
  });

  const { data: images = [] } = useQuery({
    queryKey: ['patient-images', id],
    queryFn: () => imagingApi.listImages({ patient_id: id }),
    enabled: !!id,
    retry: false,
  });

  if (isLoading) return <Center py="xl"><Loader size="lg" /></Center>;
  if (!patient) return <Text>Patient not found.</Text>;

  if (patient) setSelectedPatient(patient);

  return (
    <Stack>
      <PatientBanner patient={patient} />

      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<RiUserLine size={16} />}>Overview</Tabs.Tab>
          <Tabs.Tab value="plans" leftSection={<RiFileList3Line size={16} />}>
            Treatment Plans {plans.length > 0 && <Badge size="xs" ml={4}>{plans.length}</Badge>}
          </Tabs.Tab>
          <Tabs.Tab value="treatment" leftSection={<RiPulseLine size={16} />}>Treatment History</Tabs.Tab>
          <Tabs.Tab value="images" leftSection={<RiImage2Line size={16} />}>
            Images {images.length > 0 && <Badge size="xs" ml={4}>{images.length}</Badge>}
          </Tabs.Tab>
          <Tabs.Tab value="timeline" leftSection={<RiTimeLine size={16} />}>Timeline</Tabs.Tab>
        </Tabs.List>

        {/* Overview */}
        <Tabs.Panel value="overview" pt="md">
          <Card withBorder p="md">
            <Title order={4} mb="md">Demographics</Title>
            <Table>
              <Table.Tbody>
                <Table.Tr><Table.Td fw={600} w={200}>Full Name</Table.Td><Table.Td>{patient.last_name}, {patient.first_name}{patient.middle_name ? ` ${patient.middle_name}` : ''}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>MRN</Table.Td><Table.Td>{patient.mrn}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>Date of Birth</Table.Td><Table.Td>{patient.date_of_birth}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>Sex</Table.Td><Table.Td>{patient.sex}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>Phone</Table.Td><Table.Td>{patient.phone_primary || '—'}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>Email</Table.Td><Table.Td>{patient.email || '—'}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>Address</Table.Td><Table.Td>{patient.address_line1 || '—'}{patient.city ? `, ${patient.city}` : ''}{patient.state ? `, ${patient.state}` : ''}{patient.postal_code ? ` ${patient.postal_code}` : ''}</Table.Td></Table.Tr>
                <Table.Tr><Table.Td fw={600}>DICOM Patient ID</Table.Td><Table.Td>{patient.dicom_patient_id || '—'}</Table.Td></Table.Tr>
              </Table.Tbody>
            </Table>
          </Card>

          {patient.diagnoses && patient.diagnoses.length > 0 && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Diagnoses</Title>
              <Table>
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>ICD-10</Table.Th><Table.Th>Description</Table.Th><Table.Th>Site</Table.Th>
                    <Table.Th>Laterality</Table.Th><Table.Th>Date</Table.Th><Table.Th>Primary</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {patient.diagnoses.map((dx) => (
                    <Table.Tr key={dx.id}>
                      <Table.Td fw={600}>{dx.icd10_code}</Table.Td>
                      <Table.Td>{dx.description}</Table.Td>
                      <Table.Td>{dx.site || '—'}</Table.Td>
                      <Table.Td>{dx.laterality || '—'}</Table.Td>
                      <Table.Td>{dx.diagnosis_date || '—'}</Table.Td>
                      <Table.Td>{dx.is_primary && <Badge color="blue" size="xs">Primary</Badge>}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Card>
          )}

          {patient.allergies && patient.allergies.length > 0 && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Allergies</Title>
              <Group>
                {patient.allergies.map((allergy) => (
                  <Badge key={allergy.id} color="red" variant="light" size="lg">
                    {allergy.allergen}{allergy.severity ? ` (${allergy.severity})` : ''}
                  </Badge>
                ))}
              </Group>
            </Card>
          )}

          {patient.notes && (
            <Card withBorder p="md" mt="md">
              <Title order={4} mb="md">Notes</Title>
              <Text>{patient.notes}</Text>
            </Card>
          )}
        </Tabs.Panel>

        {/* Treatment Plans */}
        <Tabs.Panel value="plans" pt="md">
          {courses.length > 0 && (
            <Card withBorder p="md" mb="md">
              <Title order={4} mb="md">Treatment Courses</Title>
              <Table striped>
                <Table.Thead>
                  <Table.Tr><Table.Th>Course</Table.Th><Table.Th>Intent</Table.Th><Table.Th>Start Date</Table.Th><Table.Th>Status</Table.Th></Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {courses.map((course) => (
                    <Table.Tr key={course.id}>
                      <Table.Td fw={600}>Course {course.course_number}</Table.Td>
                      <Table.Td><Badge variant="light">{course.intent}</Badge></Table.Td>
                      <Table.Td>{course.start_date || '—'}</Table.Td>
                      <Table.Td><Badge color={course.status === 'active' ? 'green' : 'gray'}>{course.status}</Badge></Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </Card>
          )}

          {plans.length > 0 ? (
            <Stack>
              {plans.map((plan) => (
                <Card key={plan.id} withBorder p="md">
                  <Group justify="space-between" mb="sm">
                    <div>
                      <Text fw={600} size="lg">{plan.plan_label}</Text>
                      {plan.plan_name && <Text size="sm" c="dimmed">{plan.plan_name}</Text>}
                    </div>
                    <Badge color={planStatusColor[plan.status] || 'gray'} size="lg">{plan.status.replace('_', ' ')}</Badge>
                  </Group>
                  <Divider mb="sm" />
                  <Group gap="xl">
                    <div><Text size="xs" c="dimmed">Version</Text><Text size="sm" fw={500}>{plan.version}</Text></div>
                    <div><Text size="xs" c="dimmed">Beams</Text><Text size="sm" fw={500}>{plan.num_beams || '—'}</Text></div>
                    <div><Text size="xs" c="dimmed">Fractions</Text><Text size="sm" fw={500}>{plan.num_fractions_planned || '—'}</Text></div>
                    <div><Text size="xs" c="dimmed">Created</Text><Text size="sm" fw={500}>{new Date(plan.created_at).toLocaleDateString()}</Text></div>
                    {plan.approved_at && <div><Text size="xs" c="dimmed">Approved</Text><Text size="sm" fw={500}>{new Date(plan.approved_at).toLocaleDateString()}</Text></div>}
                  </Group>
                  {plan.beams && plan.beams.length > 0 && (
                    <>
                      <Divider my="sm" />
                      <Text size="sm" fw={600} mb="xs">Beams</Text>
                      <Table>
                        <Table.Thead>
                          <Table.Tr><Table.Th>#</Table.Th><Table.Th>Name</Table.Th><Table.Th>Type</Table.Th><Table.Th>Energy</Table.Th><Table.Th>MU</Table.Th><Table.Th>Gantry</Table.Th></Table.Tr>
                        </Table.Thead>
                        <Table.Tbody>
                          {plan.beams.map((beam) => (
                            <Table.Tr key={beam.id}>
                              <Table.Td>{beam.beam_number}</Table.Td>
                              <Table.Td fw={500}>{beam.beam_name || '—'}</Table.Td>
                              <Table.Td>{beam.beam_type}</Table.Td>
                              <Table.Td>{beam.energy_label || `${beam.energy_mev} MeV`}</Table.Td>
                              <Table.Td>{beam.planned_mu?.toFixed(1) || '—'}</Table.Td>
                              <Table.Td>{beam.gantry_angle != null ? `${beam.gantry_angle}°` : '—'}</Table.Td>
                            </Table.Tr>
                          ))}
                        </Table.Tbody>
                      </Table>
                    </>
                  )}
                </Card>
              ))}
            </Stack>
          ) : (
            <Card withBorder p="md"><Text c="dimmed" ta="center" py="xl">No treatment plans found for this patient.</Text></Card>
          )}
        </Tabs.Panel>

        {/* Treatment History */}
        <Tabs.Panel value="treatment" pt="md">
          {doseSummary ? (
            <Stack>
              <Card withBorder p="md">
                <Title order={4} mb="md">Dose Summary</Title>
                <Group gap="xl" mb="md">
                  <div><Text size="xs" c="dimmed">Total Prescribed</Text><Text size="lg" fw={700}>{(doseSummary.total_prescribed_dose_cgy / 100).toFixed(1)} Gy</Text></div>
                  <div><Text size="xs" c="dimmed">Total Delivered</Text><Text size="lg" fw={700} c="green">{(doseSummary.total_delivered_dose_cgy / 100).toFixed(1)} Gy</Text></div>
                  <div><Text size="xs" c="dimmed">Fractions</Text><Text size="lg" fw={700}>{doseSummary.fractions_completed} / {doseSummary.fractions_completed + doseSummary.fractions_remaining}</Text></div>
                </Group>
                <Progress value={doseSummary.total_prescribed_dose_cgy > 0 ? (doseSummary.total_delivered_dose_cgy / doseSummary.total_prescribed_dose_cgy) * 100 : 0} color="green" size="xl" />
              </Card>
              {doseSummary.courses.map((course) => (
                <Card key={course.course_id} withBorder p="md">
                  <Group justify="space-between" mb="sm">
                    <Text fw={600}>Course {course.course_number}</Text>
                    <Badge color={course.fractions_completed === course.fractions_total ? 'green' : 'blue'}>{course.fractions_completed}/{course.fractions_total} fractions</Badge>
                  </Group>
                  <Group gap="xl" mb="xs">
                    <div><Text size="xs" c="dimmed">Prescribed</Text><Text size="sm" fw={500}>{(course.prescribed_dose_cgy / 100).toFixed(1)} Gy</Text></div>
                    <div><Text size="xs" c="dimmed">Delivered</Text><Text size="sm" fw={500} c="green">{(course.delivered_dose_cgy / 100).toFixed(1)} Gy</Text></div>
                  </Group>
                  <Progress value={course.prescribed_dose_cgy > 0 ? (course.delivered_dose_cgy / course.prescribed_dose_cgy) * 100 : 0} color="green" size="md" />
                </Card>
              ))}
            </Stack>
          ) : (
            <Card withBorder p="md"><Text c="dimmed" ta="center" py="xl">No treatment history available. Records appear after delivery sessions.</Text></Card>
          )}
        </Tabs.Panel>

        {/* Images */}
        <Tabs.Panel value="images" pt="md">
          {images.length > 0 ? (
            <Stack>
              {images.map((img) => (
                <Paper key={img.id} withBorder p="md" radius="sm">
                  <Group justify="space-between">
                    <div>
                      <Group gap="xs" mb={4}>
                        <Badge size="sm" variant="light">{img.image_type}</Badge>
                        <Text size="sm" fw={600}>{img.rt_image_description || 'Untitled image'}</Text>
                      </Group>
                      <Text size="xs" c="dimmed">
                        Acquired: {new Date(img.acquisition_date || img.created_at).toLocaleDateString()}
                        {img.gantry_angle != null && ` | Gantry: ${img.gantry_angle}°`}
                      </Text>
                    </div>
                    <Badge color="blue" variant="light">{img.modality || img.image_type}</Badge>
                  </Group>
                </Paper>
              ))}
            </Stack>
          ) : (
            <Card withBorder p="md"><Text c="dimmed" ta="center" py="xl">No images found for this patient.</Text></Card>
          )}
        </Tabs.Panel>

        {/* Timeline */}
        <Tabs.Panel value="timeline" pt="md">
          <Card withBorder p="md">
            <Title order={4} mb="md">Patient Timeline</Title>
            <Timeline active={999} bulletSize={24} lineWidth={2}>
              <Timeline.Item bullet={<ThemeIcon size={20} variant="light" color="blue" radius="xl"><RiUserLine size={12} /></ThemeIcon>} title="Patient Registered">
                <Text size="xs" c="dimmed">{new Date(patient.created_at).toLocaleString()}</Text>
              </Timeline.Item>
              {patient.diagnoses?.map((dx) => (
                <Timeline.Item key={dx.id} bullet={<ThemeIcon size={20} variant="light" color="red" radius="xl"><RiFileList3Line size={12} /></ThemeIcon>} title={`Diagnosis: ${dx.icd10_code}`}>
                  <Text size="sm">{dx.description}</Text>
                  <Text size="xs" c="dimmed">{dx.diagnosis_date || 'Date unknown'}</Text>
                </Timeline.Item>
              ))}
              {courses.map((course) => (
                <Timeline.Item key={course.id} bullet={<ThemeIcon size={20} variant="light" color="orange" radius="xl"><RiCalendarLine size={12} /></ThemeIcon>} title={`Course ${course.course_number} — ${course.intent}`}>
                  <Text size="xs" c="dimmed">Started: {course.start_date || 'Not started'}</Text>
                </Timeline.Item>
              ))}
              {plans.map((plan) => (
                <Timeline.Item key={plan.id} bullet={<ThemeIcon size={20} variant="light" color="teal" radius="xl"><RiShieldCheckLine size={12} /></ThemeIcon>} title={`Plan: ${plan.plan_label}`}>
                  <Group gap="xs">
                    <Badge size="xs" color={planStatusColor[plan.status] || 'gray'}>{plan.status}</Badge>
                    <Text size="xs" c="dimmed">{new Date(plan.created_at).toLocaleDateString()}</Text>
                  </Group>
                </Timeline.Item>
              ))}
              {doseSummary?.courses.map((course) =>
                course.fractions_completed > 0 && (
                  <Timeline.Item key={`dose-${course.course_id}`} bullet={<ThemeIcon size={20} variant="light" color="green" radius="xl"><RiCheckLine size={12} /></ThemeIcon>} title={`Delivered ${course.fractions_completed}/${course.fractions_total} fractions`}>
                    <Text size="xs" c="dimmed">{(course.delivered_dose_cgy / 100).toFixed(1)} Gy of {(course.prescribed_dose_cgy / 100).toFixed(1)} Gy</Text>
                  </Timeline.Item>
                )
              )}
            </Timeline>
          </Card>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
