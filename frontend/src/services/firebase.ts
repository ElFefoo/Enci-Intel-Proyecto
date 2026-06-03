/**
 * Inicializacion de Firebase Auth (Identity Platform)
 * Los valores vienen de variables de entorno Vite (VITE_FIREBASE_*)
 */
import { initializeApp } from 'firebase/app'
import {
  getAuth,
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  type User,
} from 'firebase/auth'

const firebaseConfig = {
  apiKey:     import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId:  import.meta.env.VITE_FIREBASE_PROJECT_ID,
}

const app  = initializeApp(firebaseConfig)
export const firebaseAuth = getAuth(app)

/** Obtiene el ID Token actual (se refresca automaticamente cada hora). */
export async function getIdToken(): Promise<string | null> {
  const user = firebaseAuth.currentUser
  if (!user) return null
  return user.getIdToken()
}

export { signInWithEmailAndPassword, signOut, onAuthStateChanged, type User }
