/**
 * Cliente Axios — adjunta automaticamente el Firebase ID Token en cada request.
 * El token se refresca solo cuando esta proximo a vencer (Firebase SDK lo maneja).
 */
import axios from 'axios'
import { getIdToken } from './firebase'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

// Interceptor de request — agrega Bearer token
api.interceptors.request.use(async (config) => {
  const token = await getIdToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Interceptor de response — manejo global de errores
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expirado o invalido — redirigir al login
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
