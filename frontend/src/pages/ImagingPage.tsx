import { useState } from 'react';
import {
  Title, Card, Stack, Group, Button, Table, Badge, Text,
  FileInput, Select, Modal, Loader,
} from '@mantine/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { IconUpload, IconEye } from '@tabler/icons-react';
import { imagingApi } from '../api/imaging';
import type { RTImage } from '../types/imaging';

const IMAGE_TYPE_COLORS: Record<string, string> = {
  portal: 'blue',
  cbct: 'grape',
  kv: 'teal',
  mv: 'orange',
  drr: 'cyan',
  ct: 'indigo',
};

export default function ImagingPage() {
  const queryClient = useQueryClient();
  const [importModalOpen, setImportModalOpen] = useState(false);
  const [selectedImage, setSelectedImage] = useState<RTImage | null>(null);
  const [importFile, setImportFile] = useState<File | null>(null);
  const [filterType, setFilterType] = useState<string | null>(null);

  const { data: images = [], isLoading } = useQuery({
    queryKey: ['images', filterType],
    queryFn: () => imagingApi.listImages(filterType ? { image_type: filterType } : {}),
  });

  const importMutation = useMutation({
    mutationFn: (file: File) => imagingApi.importImage(file, ''),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['images'] });
      setImportModalOpen(false);
      notifications.show({ title: 'Success', message: 'Image imported', color: 'green' });
    },
  });

  return (
    <Stack>
      <Group justify="space-between">
        <Title order={2}>Image Guidance</Title>
        <Group>
          <Select
            placeholder="Filter by type"
            clearable
            value={filterType}
            onChange={setFilterType}
            data={[
              { value: 'portal', label: 'Portal' },
              { value: 'cbct', label: 'CBCT' },
              { value: 'kv', label: 'kV' },
              { value: 'drr', label: 'DRR' },
              { value: 'ct', label: 'CT' },
            ]}
          />
          <Button leftSection={<IconUpload size={16} />} onClick={() => setImportModalOpen(true)}>
            Import Image
          </Button>
        </Group>
      </Group>

      <Card withBorder>
        {isLoading ? (
          <Group justify="center" py="xl"><Loader /></Group>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>Type</Table.Th>
                <Table.Th>Modality</Table.Th>
                <Table.Th>Description</Table.Th>
                <Table.Th>Size</Table.Th>
                <Table.Th>Gantry</Table.Th>
                <Table.Th>Acquired</Table.Th>
                <Table.Th>Actions</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {images.map((image) => (
                <Table.Tr key={image.id}>
                  <Table.Td>
                    <Badge color={IMAGE_TYPE_COLORS[image.image_type] || 'gray'}>{image.image_type}</Badge>
                  </Table.Td>
                  <Table.Td>{image.modality || '-'}</Table.Td>
                  <Table.Td>{image.rt_image_description || '-'}</Table.Td>
                  <Table.Td>{image.rows && image.columns ? `${image.rows}x${image.columns}` : '-'}</Table.Td>
                  <Table.Td>{image.gantry_angle != null ? `${image.gantry_angle}°` : '-'}</Table.Td>
                  <Table.Td>
                    {image.acquisition_date ? new Date(image.acquisition_date).toLocaleDateString() : '-'}
                  </Table.Td>
                  <Table.Td>
                    <Button variant="subtle" size="xs" leftSection={<IconEye size={14} />} onClick={() => setSelectedImage(image)}>
                      View
                    </Button>
                  </Table.Td>
                </Table.Tr>
              ))}
              {images.length === 0 && (
                <Table.Tr>
                  <Table.Td colSpan={7}>
                    <Text ta="center" c="dimmed" py="xl">
                      No images found. Import DICOM images to get started.
                    </Text>
                  </Table.Td>
                </Table.Tr>
              )}
            </Table.Tbody>
          </Table>
        )}
      </Card>

      <Modal opened={importModalOpen} onClose={() => setImportModalOpen(false)} title="Import DICOM Image">
        <Stack>
          <FileInput label="DICOM Image File" placeholder="Select .dcm file" accept=".dcm" value={importFile} onChange={setImportFile} />
          <Button onClick={() => importFile && importMutation.mutate(importFile)} loading={importMutation.isPending} disabled={!importFile}>
            Import
          </Button>
        </Stack>
      </Modal>

      <Modal opened={!!selectedImage} onClose={() => setSelectedImage(null)} title="Image Details" size="xl">
        {selectedImage && (
          <Stack>
            <Group>
              <Text fw={600}>Type:</Text>
              <Badge color={IMAGE_TYPE_COLORS[selectedImage.image_type] || 'gray'}>{selectedImage.image_type}</Badge>
            </Group>
            {selectedImage.sop_instance_uid && (
              <Group>
                <Text fw={600}>SOP UID:</Text>
                <Text size="sm" style={{ fontFamily: 'monospace' }}>{selectedImage.sop_instance_uid}</Text>
              </Group>
            )}
            <Group>
              <Text fw={600}>Dimensions:</Text>
              <Text>{selectedImage.rows} x {selectedImage.columns}</Text>
            </Group>
            {selectedImage.gantry_angle != null && (
              <Group>
                <Text fw={600}>Gantry Angle:</Text>
                <Text>{selectedImage.gantry_angle}°</Text>
              </Group>
            )}
            <Card withBorder bg="dark.9" h={300}>
              <Group justify="center" align="center" h="100%">
                <Text c="dimmed">DICOM Viewer (Cornerstone3D integration)</Text>
              </Group>
            </Card>
          </Stack>
        )}
      </Modal>
    </Stack>
  );
}
