import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './services/authStore'
import AppLayout from './components/AppLayout'
import LoginPage from './pages/LoginPage'
import CodingPage from './pages/CodingPage'
import DRGPage from './pages/DRGPage'
import QCPage from './pages/QCPage'
import PipelinePage from './pages/PipelinePage'
import DashboardPage from './pages/DashboardPage'
import GuidePage from './pages/GuidePage'
import AdminPage from './pages/AdminPage'
import NotFoundPage from './pages/NotFoundPage'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" />
}

function AdminRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user)
  if (user?.role !== 'admin') return <Navigate to="/pipeline" />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/pipeline" />} />
        <Route path="pipeline" element={<PipelinePage />} />
        <Route path="coding" element={<CodingPage />} />
        <Route path="drg" element={<DRGPage />} />
        <Route path="qc" element={<QCPage />} />
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="guide" element={<GuidePage />} />
        <Route path="admin" element={<AdminRoute><AdminPage /></AdminRoute>} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
