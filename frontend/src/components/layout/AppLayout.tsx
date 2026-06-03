import { Outlet, NavLink, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../../store/authStore'
import {
  LayoutDashboard, Bell, Bot, Package,
  Map, MessageSquare, FileText, LogOut
} from 'lucide-react'

const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/alerts',   icon: Bell,            label: 'Alertas' },
  { to: '/agents',   icon: Bot,             label: 'Agentes IA' },
  { to: '/products', icon: Package,         label: 'Productos' },
  { to: '/market',   icon: Map,             label: 'Mapa Competitivo' },
  { to: '/chat',     icon: MessageSquare,   label: 'Consultor IA' },
  { to: '/reports',  icon: FileText,        label: 'Reportes' },
]

export default function AppLayout() {
  const { user, role, logout } = useAuthStore()
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/login')
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-60 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-4 border-b border-gray-100">
          <svg viewBox="0 0 32 32" fill="none" className="w-7 h-7 flex-shrink-0">
            <rect width="32" height="32" rx="8" fill="#01696F"/>
            <path d="M8 16 L14 10 L20 16 L14 22 Z" fill="white" opacity="0.9"/>
            <path d="M16 8 L24 16 L16 24" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
          </svg>
          <span className="font-bold text-gray-900">Enci-Intel</span>
        </div>

        {/* Nav */}
        <nav className="flex-1 px-3 py-4 space-y-0.5">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive
                    ? 'bg-teal-50 text-teal-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`
              }
            >
              <Icon size={16} />
              {label}
            </NavLink>
          ))}
        </nav>

        {/* User */}
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="text-xs text-gray-500 truncate mb-1">{user?.email}</div>
          <div className="flex items-center justify-between">
            <span className="text-xs bg-teal-100 text-teal-700 px-2 py-0.5 rounded-full font-medium">
              {role}
            </span>
            <button
              onClick={handleLogout}
              className="text-gray-400 hover:text-gray-700 transition-colors"
              title="Cerrar sesión"
            >
              <LogOut size={15} />
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-auto">
        <Outlet />
      </main>
    </div>
  )
}
