/**
 * Store de autenticacion — Firebase Auth + Zustand
 *
 * Flujo:
 *  1. Usuario hace login con email/password
 *  2. Firebase emite ID Token con custom claim 'role'
 *  3. El token se adjunta automaticamente en cada request via api.ts interceptor
 *  4. El rol determina que rutas y acciones estan disponibles
 */
import { create } from 'zustand'
import {
  firebaseAuth,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  getIdToken,
  type User,
} from '../services/firebase'

export type Role = 'Admin' | 'Comercial' | 'Gerencia'

interface AuthState {
  user: User | null
  role: Role | null
  loading: boolean
  error: string | null
  // Actions
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  init: () => () => void   // retorna el unsubscribe de onAuthStateChanged
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  role: null,
  loading: true,
  error: null,

  login: async (email, password) => {
    set({ loading: true, error: null })
    try {
      await signInWithEmailAndPassword(firebaseAuth, email, password)
      // El rol se carga en init() via onAuthStateChanged
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error al iniciar sesion'
      set({ error: msg, loading: false })
      throw err
    }
  },

  logout: async () => {
    await signOut(firebaseAuth)
    set({ user: null, role: null })
  },

  init: () => {
    const unsubscribe = onAuthStateChanged(firebaseAuth, async (user) => {
      if (user) {
        // Forzar refresh para obtener custom claims actualizados
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
