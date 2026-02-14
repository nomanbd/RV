import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/common/Layout';
import ProtectedRoute from './components/common/ProtectedRoute';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import PatientListPage from './pages/PatientListPage';
import PatientDetailPage from './pages/PatientDetailPage';
import PlanManagementPage from './pages/PlanManagementPage';
import TreatmentConsolePage from './pages/TreatmentConsolePage';
import ImagingPage from './pages/ImagingPage';
import SchedulingPage from './pages/SchedulingPage';
import ReportingPage from './pages/ReportingPage';
import MachineManagementPage from './pages/MachineManagementPage';
import UserManagementPage from './pages/UserManagementPage';
import QAPage from './pages/QAPage';
import AuditLogPage from './pages/AuditLogPage';
import SettingsPage from './pages/SettingsPage';
import OISIntegrationPage from './pages/OISIntegrationPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />

        <Route
          element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardPage />} />

          {/* Patients */}
          <Route path="/patients" element={<PatientListPage />} />
          <Route path="/patients/:id" element={<PatientDetailPage />} />

          {/* Planning */}
          <Route path="/plans" element={<PlanManagementPage />} />

          {/* Treatment */}
          <Route path="/treatment" element={<TreatmentConsolePage />} />

          {/* Imaging */}
          <Route path="/imaging" element={<ImagingPage />} />

          {/* Scheduling */}
          <Route path="/scheduling" element={<SchedulingPage />} />

          {/* Reporting */}
          <Route path="/reports" element={<ReportingPage />} />

          {/* Admin */}
          <Route path="/admin/machines" element={<MachineManagementPage />} />
          <Route path="/admin/users" element={<UserManagementPage />} />
          <Route path="/admin/qa" element={<QAPage />} />
          <Route path="/admin/audit" element={<AuditLogPage />} />
          <Route path="/admin/settings" element={<SettingsPage />} />
          <Route path="/admin/ois" element={<OISIntegrationPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
