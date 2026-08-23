import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import DailyLogPage from './pages/DailyLogPage'
import DoctorModePage from './pages/DoctorModePage'
import DocumentsPage from './pages/DocumentsPage'
import HomePage from './pages/HomePage'
import HealthGuardPage from './pages/HealthGuardPage'
import MemberPage from './pages/MemberPage'
import MedicalKnowledgePage from './pages/MedicalKnowledgePage'
import MedicationCoursesPage from './pages/MedicationCoursesPage'
import MembersPage from './pages/MembersPage'
import NotFoundPage from './pages/NotFoundPage'
import SettingsPage from './pages/SettingsPage'
import TasksPage from './pages/TasksPage'
import VisitPage from './pages/VisitPage'

export default function App() {
  return <Routes><Route element={<Layout />}><Route path="/" element={<HomePage />} /><Route path="/members" element={<MembersPage />} /><Route path="/members/:id" element={<MemberPage />} /><Route path="/health-guard/:memberId" element={<HealthGuardPage />} /><Route path="/medical-knowledge" element={<MedicalKnowledgePage />} /><Route path="/medication-courses/:memberId" element={<MedicationCoursesPage />} /><Route path="/doctor-mode/:memberId" element={<DoctorModePage />} /><Route path="/visits/:visitId" element={<VisitPage />} /><Route path="/daily-log/:memberId" element={<DailyLogPage />} /><Route path="/documents/:memberId" element={<DocumentsPage />} /><Route path="/tasks/:memberId" element={<TasksPage />} /><Route path="/settings" element={<SettingsPage />} /><Route path="*" element={<NotFoundPage />} /></Route></Routes>
}
