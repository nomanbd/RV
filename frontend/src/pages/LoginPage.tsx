import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Paper,
  TextInput,
  PasswordInput,
  Button,
  Title,
  Text,
  Alert,
  Stack,
  Center,
  Group,
} from '@mantine/core';
import { RiPulseLine, RiAlertLine } from 'react-icons/ri';
import { authApi } from '../api/auth';
import { useAppStore } from '../store';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();
  const { setAuth } = useAppStore();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const tokens = await authApi.login({ username, password });
      localStorage.setItem('access_token', tokens.access_token);
      localStorage.setItem('refresh_token', tokens.refresh_token);

      const user = await authApi.getMe();
      setAuth(user, tokens.access_token, tokens.refresh_token);
      navigate('/');
    } catch (err: unknown) {
      const message = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container size={420} my={100}>
      <Center mb="xl">
        <Group>
          <RiPulseLine size={40} color="var(--mantine-color-blue-6)" />
          <div>
            <Title order={2} c="blue.7">RadOnc R&V</Title>
            <Text size="xs" c="dimmed">Record & Verify System</Text>
          </div>
        </Group>
      </Center>

      <Paper withBorder shadow="md" p={30} radius="md">
        <Title order={3} mb="md" ta="center">Sign In</Title>

        <form onSubmit={handleLogin}>
          <Stack>
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
              autoFocus
            />

            <PasswordInput
              label="Password"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.currentTarget.value)}
              required
            />

            <Button type="submit" fullWidth loading={loading}>
              Sign In
            </Button>
          </Stack>
        </form>

        <Text c="dimmed" size="xs" ta="center" mt="md">
          Authorized personnel only. All access is logged.
        </Text>
      </Paper>
    </Container>
  );
}
