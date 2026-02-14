import { Title, Card, Text, Stack, SimpleGrid } from '@mantine/core';
import {
  RiFileList3Line,
  RiBarChartLine,
  RiShieldCheckLine,
  RiHospitalLine,
} from 'react-icons/ri';

function ReportCard({ title, description, icon: Icon }: {
  title: string;
  description: string;
  icon: React.ComponentType<{ size: number }>;
}) {
  return (
    <Card withBorder p="md" style={{ cursor: 'pointer' }}>
      <Icon size={32} />
      <Text fw={600} mt="sm">{title}</Text>
      <Text size="sm" c="dimmed">{description}</Text>
    </Card>
  );
}

export default function ReportingPage() {
  return (
    <Stack>
      <Title order={2}>Reports & Analytics</Title>
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }}>
        <ReportCard
          title="Treatment Summary"
          description="Patient treatment delivery summary with dose tracking"
          icon={RiFileList3Line}
        />
        <ReportCard
          title="Dose Tracking"
          description="Cumulative dose reports across treatment courses"
          icon={RiBarChartLine}
        />
        <ReportCard
          title="QA Summary"
          description="Quality assurance metrics and compliance reports"
          icon={RiShieldCheckLine}
        />
        <ReportCard
          title="Machine Utilization"
          description="Treatment machine usage and availability reports"
          icon={RiHospitalLine}
        />
      </SimpleGrid>
    </Stack>
  );
}
