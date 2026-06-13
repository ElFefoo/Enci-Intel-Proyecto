import { Routes, Route, NavLink } from 'react-router-dom'
import ConsultorIA from './pages/ConsultorIA'

function Sidebar() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all ${
      isActive
        ? 'bg-green-600 text-white'
        : 'text-gray-600 hover:bg-gray-100'
    }`

  return (
    <aside className="w-56 shrink-0 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-5 py-5 border-b border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-green-600 flex items-center justify-center">
            <span className="text-white font-bold text-xs">EI</span>
          </div>
          <div>
            <p className="font-bold text-gray-900 text-sm">Enci-Intel</p>
            <p className="text-xs text-gray-400">Encipharm</p>
          </div>
        </div>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        <NavLink to="/" end className={linkClass}>📊 Dashboard</NavLink>
        <NavLink to="/alertas" className={linkClass}>🔔 Alertas</NavLink>
        <NavLink to="/agentes" className={linkClass}>🤖 Agentes IA</NavLink>
        <NavLink to="/productos" className={linkClass}>💊 Productos</NavLink>
        <NavLink to="/mapa" className={linkClass}>🗺️ Mapa Competitivo</NavLink>
        <NavLink to="/consultor" className={linkClass}>🐄 Consultor Vet IA</NavLink>
        <NavLink to="/reportes" className={linkClass}>📄 Reportes</NavLink>
      </nav>
      <div className="p-4 border-t border-gray-100">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-blue-700 font-bold text-xs">
            A
          </div>
          <div>
            <p className="text-xs font-medium text-gray-700">Dev Admin</p>
            <p className="text-xs text-gray-400">admin@encipharm.cl</p>
          </div>
        </div>
      </div>
    </aside>
  )
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex items-center justify-center h-full">
      <div className="text-center">
        <p className="text-4xl mb-3">🚧</p>
        <h2 className="text-lg font-semibold text-gray-600">{title}</h2>
        <p className="text-sm text-gray-400 mt-1">Módulo en desarrollo</p>
      </div>
    </div>
  )
}

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar />
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<PlaceholderPage title="Dashboard" />} />
          <Route path="/alertas" element={<PlaceholderPage title="Alertas" />} />
          <Route path="/agentes" element={<PlaceholderPage title="Agentes IA" />} />
          <Route path="/productos" element={<PlaceholderPage title="Productos" />} />
          <Route path="/mapa" element={<PlaceholderPage title="Mapa Competitivo" />} />
          <Route path="/consultor" element={<ConsultorIA />} />
          <Route path="/reportes" element={<PlaceholderPage title="Reportes" />} />
        </Routes>
      </main>
    </div>
  )
}
