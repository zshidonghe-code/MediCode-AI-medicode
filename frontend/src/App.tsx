import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Spin } from 'antd'
import { useAuthStore } from './services/authStore'
import AppLayout from './components/AppLayout'

const LoginPage = lazy(() => import('./pages/LoginPage'))
const CodingPage = lazy(() => import('./pages/CodingPage'))
const DRGPage = lazy(() => import('./pages/DRGPage'))
const QCPage = lazy(() => import('./pages/QCPage'))
const PipelinePage = lazy(() => import('./pages/PipelinePage'))
const DashboardPage = lazy(() => import('./pages/DashboardPage'))
const GuidePage = lazy(() => import('./pages/GuidePage'))
const AdminPage = lazy(() => import('./pages/AdminPage'))
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'))

function LazyLoad({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%' }}><Spin size="large" /></div>}>{children}</Suspense>
}

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
      <Route path="/login" element={<LazyLoad><LoginPage /></LazyLoad>} />
      <Route
        path="/"
        element={
          <PrivateRoute>
            <AppLayout />
          </PrivateRoute>
        }
      >
        <Route index element={<Navigate to="/pipeline" />} />
        <Route path="pipeline" element={<LazyLoad><PipelinePage /></LazyLoad>} />
        <Route path="coding" element={<LazyLoad><CodingPage /></LazyLoad>} />
        <Route path="drg" element={<LazyLoad><DRGPage /></LazyLoad>} />
        <Route path="qc" element={<LazyLoad><QCPage /></LazyLoad>} />
        <Route path="dashboard" element={<LazyLoad><DashboardPage /></LazyLoad>} />
        <Route path="guide" element={<LazyLoad><GuidePage /></LazyLoad>} />
        <Route path="admin" element={<LazyLoad><AdminRoute><AdminPage /></AdminRoute></LazyLoad>} />
        <Route path="*" element={<LazyLoad><NotFoundPage /></LazyLoad>} />
      </Route>
    </Routes>
  )
}
