import type { ChatQueryRequest, SSEToken } from '../types/chat'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

/**
 * Envía una consulta al Consultor IA y consume el stream SSE.
 * Llama onToken por cada token recibido y onDone al finalizar.
 */
export async function streamChatQuery(
  request: ChatQueryRequest,
  onToken: (token: string) => void,
  onDone: (sessionId?: string) => void,
  onError: (message: string) => void,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${API_BASE}/api/v1/chat/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
    signal,
  })

  if (!response.ok || !response.body) {
    onError(`Error ${response.status}: no se pudo conectar al servidor`)
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    const chunk = decoder.decode(value, { stream: true })
    const lines = chunk.split('\n').filter(l => l.startsWith('data: '))

    for (const line of lines) {
      try {
        const raw = line.replace('data: ', '').trim()
        const parsed: SSEToken = JSON.parse(raw)

        if (parsed.type === 'token' && parsed.content) {
          onToken(parsed.content)
        } else if (parsed.type === 'done') {
          onDone(parsed.session_id)
        } else if (parsed.type === 'error') {
          onError(parsed.message ?? 'Error desconocido')
        }
      } catch {
        // chunk parcial, ignorar
      }
    }
  }
}

export async function getChatHistory() {
  const res = await fetch(`${API_BASE}/api/v1/chat/history`)
  if (!res.ok) return []
  const data = await res.json()
  return data.data ?? []
}

export async function clearChatHistory() {
  await fetch(`${API_BASE}/api/v1/chat/history`, { method: 'DELETE' })
}
