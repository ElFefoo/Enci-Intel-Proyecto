/**
 * Firebase Auth SDK
 * Si VITE_DISABLE_AUTH=true, las funciones son no-ops seguros.
 */
import { initializeApp } from 'firebase/app'
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  type User,
} from 'firebase/auth'

const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true'

// Solo inicializa Firebase si auth esta habilitada
const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY     ?? 'mock',
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN ?? 'mock.firebaseapp.com',
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID  ?? 'mock-project',
}

const app = initializeApp(firebaseConfig)
export const firebaseAuth = getAuth(app)

export async function getIdToken(): Promise<string | null> {
  if (DISABLE_AUTH) return 'dev-mock-token'
  const user = firebaseAuth.currentUser
  if (!user) return null
  return user.getIdToken()
}

export { signInWithEmailAndPassword, signOut, onAuthStateChanged, type User }
