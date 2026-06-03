/**
 * Store de autenticacion — Firebase Auth + Zustand
 * Con soporte para VITE_DISABLE_AUTH=true en desarrollo local
 */
import { create } from 'zustand'
import {
  firebaseAuth,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  type User,
} from '../services/firebase'

export type Role = 'Admin' | 'Comercial' | 'Gerencia'

const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true'

// Usuario mock para desarrollo local
const MOCK_USER = {
  uid: 'dev-mock-uid-001',
  email: 'admin@encipharm.cl',
  displayName: 'Dev Admin',
} as unknown as User

const MOCK_ROLE: Role = 'Admin'

interface AuthState {
  user: User | null
  role: Role | null
  loading: boolean
  error: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  init: () => () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  role: null,
  loading: true,
  error: null,

  login: async (email, password) => {
    // En modo dev: cualquier email/password pasa
    if (DISABLE_AUTH) {
      set({ user: MOCK_USER, role: MOCK_ROLE, loading: false, error: null })
      return
    }
    set({ loading: true, error: null })
    try {
      await signInWithEmailAndPassword(firebaseAuth, email, password)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al iniciar sesion'
      set({ error: msg, loading: false })
      throw err
    }
  },

  logout: async () => {
    if (!DISABLE_AUTH) await signOut(firebaseAuth)
    set({ user: null, role: null })
  },

  init: () => {
    // En modo dev: auto-login inmediato sin Firebase
    if (DISABLE_AUTH) {
      set({ user: MOCK_USER, role: MOCK_ROLE, loading: false })
      return () => {}
    }
    const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
      if (user) {
        const token = await user.getIdTokenResult(true)
        const role = (token.claims['role'] as Role) ?? null
        set({ user, role, loading: false, error: null })
      } else {
        set({ user: null, role: null, loading: false })
      }
    })
    return unsubscribe
  },
}))
