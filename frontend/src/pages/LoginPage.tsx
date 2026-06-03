import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const { login, loading, error } = useAuthStore()
  const navigate = useNavigate()

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    try {
      await login(email, password)
      navigate('/')
    } catch {
      // El error ya esta en el store
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white rounded-xl shadow-md p-8 w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center gap-3 mb-8">
          <svg viewBox="0 0 32 32" fill="none" className="w-8 h-8">
            <rect width="32" height="32" rx="8" fill="#01696F"/>
            <path d="M8 16 L14 10 L20 16 L14 22 Z" fill="white" opacity="0.9"/>
            <path d="M16 8 L24 16 L16 24" stroke="white" strokeWidth="2.5" fill="none" strokeLinecap="round"/>
          </svg>
          <span className="font-bold text-xl text-gray-900">Enci-Intel</span>
        </div>

        <h1 className="text-2xl font-semibold text-gray-900 mb-1">Iniciar sesion</h1>
        <p className="text-gray-500 text-sm mb-6">Plataforma de Inteligencia Competitiva</p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Correo electronico</label>
            <input
              type="email" required autoComplete="email"
              value={email} onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 text-sm"
              placeholder="usuario@encipharm.cl"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Contrasena</label>
            <input
              type="password" required autoComplete="current-password"
              value={password} onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-600 text-sm"
              placeholder="••••••••"
            />
          </div>

          {error && (
            <p className="text-red-600 text-sm bg-red-50 rounded-lg px-3 py-2">{error}</p>
          )}

          <button
            type="submit" disabled={loading}
            className="w-full bg-teal-700 hover:bg-teal-800 text-white font-medium py-2.5 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Iniciando sesion...' : 'Ingresar'}
          </button>
        </form>

        <p className="text-xs text-gray-400 text-center mt-6">
          Acceso restringido · Encipharm S.A.
        </p>
      </div>
    </div>
  )
}
