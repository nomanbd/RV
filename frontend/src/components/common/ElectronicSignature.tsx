import { useState } from 'react';
import {
  Modal,
  TextInput,
  PasswordInput,
  Select,
  Textarea,
  Button,
  Stack,
  Alert,
  Text,
  Group,
} from '@mantine/core';
import { RiShieldCheckLine, RiAlertLine } from 'react-icons/ri';
import { authApi } from '../../api/auth';
import type { ElectronicSignatureResponse } from '../../types/auth';

interface ElectronicSignatureProps {
  opened: boolean;
  onClose: () => void;
  onSigned: (signature: ElectronicSignatureResponse) => void;
  entityType: string;
  entityId: string;
  title?: string;
  requiredMeaning?: string;
}

const MEANING_OPTIONS = [
  { value: 'approval', label: 'Approval — I approve this action' },
  { value: 'review', label: 'Review — I have reviewed this item' },
  { value: 'verification', label: 'Verification — I verify this is correct' },
  { value: 'authorization', label: 'Authorization — I authorize this override' },
  { value: 'acknowledgment', label: 'Acknowledgment — I acknowledge this event' },
];

export default function ElectronicSignature({
  opened,
  onClose,
  onSigned,
  entityType,
  entityId,
  title = 'Electronic Signature Required',
  requiredMeaning,
}: ElectronicSignatureProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [meaning, setMeaning] = useState(requiredMeaning || 'approval');
  const [reason, setReason] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const signature = await authApi.createElectronicSignature({
        username,
        password,
        meaning: meaning as 'approval',
        reason: reason || undefined,
        entity_type: entityType,
        entity_id: entityId,
      });
      onSigned(signature);
      handleClose();
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(message || 'Signature failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setUsername('');
    setPassword('');
    setReason('');
    setError('');
    onClose();
  };

  return (
    <Modal opened={opened} onClose={handleClose} title={title} size="md">
      <Stack>
        <Alert icon={<RiShieldCheckLine />} color="blue" variant="light">
          <Text size="sm">
            21 CFR Part 11 Compliance: Re-enter your credentials to create a legally
            binding electronic signature.
          </Text>
        </Alert>

        {error && (
          <Alert icon={<RiAlertLine />} color="red" variant="light">
            {error}
          </Alert>
        )}

        <TextInput
          label="Username"
          placeholder="Enter your username"
          value={username}
          onChange={(e) => setUsername(e.currentTarget.value)}
          required
        />

        <PasswordInput
          label="Password"
          placeholder="Enter your password"
          value={password}
          onChange={(e) => setPassword(e.currentTarget.value)}
          required
        />

        <Select
          label="Signature Meaning"
          data={MEANING_OPTIONS}
          value={meaning}
          onChange={(v) => setMeaning(v || 'approval')}
          disabled={!!requiredMeaning}
          required
        />

        <Textarea
          label="Reason / Comment"
          placeholder="Optional reason for this action"
          value={reason}
          onChange={(e) => setReason(e.currentTarget.value)}
          minRows={2}
        />

        <Group justify="flex-end">
          <Button variant="subtle" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            leftSection={<RiShieldCheckLine />}
            onClick={handleSubmit}
            loading={loading}
          >
            Sign
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
