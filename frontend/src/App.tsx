import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuthStore } from './store/authStore'
import AppLayout from './components/layout/AppLayout'
import LoginPage from './pages/LoginPage'
import Dashboard from './pages/Dashboard'
import Alerts from './pages/Alerts'
import AgentsPage from './pages/AgentsPage'
import Products from './pages/Products'
import MarketMap from './pages/MarketMap'
import VetChat from './pages/VetChat'
import Reports from './pages/Reports'

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuthStore()
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-700" />
      </div>
    )
  }
  if (!user) return <Navigate to="/login" replace />
  return <>{children}</>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index     element={<Dashboard />} />
        <Route path="alerts"   element={<Alerts />} />
        <Route path="agents"   element={<AgentsPage />} />
        <Route path="products" element={<Products />} />
        <Route path="market"   element={<MarketMap />} />
        <Route path="chat"     element={<VetChat />} />
        <Route path="reports"  element={<Reports />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
