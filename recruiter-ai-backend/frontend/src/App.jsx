import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import Login from './pages/Login'
import Register from './pages/Register'
import Dashboard from './pages/Dashboard'
import RunAgent from './pages/RunAgent'
import Leads from './pages/Leads'
import LeadDetail from './pages/LeadDetail'
import Metrics from './pages/Metrics'

function App() {
  const { token, user } = useAuthStore()
  const isAuthenticated = !!token

  if (!isAuthenticated) {
    return (
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    )
  }

  return (
    <Routes>
      <Route path="/" element={<Dashboard />} />
      <Route path="/run-agent" element={<RunAgent />} />
      <Route path="/leads" element={<Leads />} />
      <Route path="/leads/:id" element={<LeadDetail />} />
      <Route path="/metrics" element={<Metrics />} />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  )
}

export default App
