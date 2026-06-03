/**
 * Cliente Axios — adjunta Bearer token en cada request.
 * En modo DISABLE_AUTH envia un token mock (el backend lo acepta con DISABLE_AUTH=true)
 */
import axios from 'axios'
import { getIdToken } from './firebase'

const DISABLE_AUTH = import.meta.env.VITE_DISABLE_AUTH === 'true'

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use(async (config) => {
  if (DISABLE_AUTH) {
    // Token mock — el backend con DISABLE_AUTH=true lo ignora
    config.headers.Authorization = 'Bearer dev-mock-token'
    return config
  }
  const token = await getIdToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401 && !DISABLE_AUTH) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
