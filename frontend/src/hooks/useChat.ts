import { useState, useRef, useCallback } from 'react'
import type { ChatMessage, Species } from '../types/chat'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

export function useChat(initialSessionId?: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sessionId, setSessionId] = useState<string | undefined>(initialSessionId)
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (
    question: string,
    species?: Species,
    category?: string,
  ) => {
    if (!question.trim() || isStreaming) return
    setError(null)

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: question,
      species,
      category,
      createdAt: new Date(),
    }
    const assistantMsgId = crypto.randomUUID()
    const assistantMsg: ChatMessage = {
      id: assistantMsgId,
      role: 'assistant',
      content: '',
      createdAt: new Date(),
      isStreaming: true,
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsStreaming(true)

    const ctrl = new AbortController()
    abortRef.current = ctrl

    try {
      const res = await fetch(`${API_BASE}/chat/query`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question,
          species: species ?? null,
          category: category ?? null,
          session_id: sessionId ?? null,
        }),
        signal: ctrl.signal,
      })

      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        const code = data?.detail?.code ?? 'ERROR'
        const msg = data?.detail?.message ?? `Error ${res.status}`
        const friendly: Record<string, string> = {
          RATE_LIMIT_EXCEEDED: '⚠️ Alcanzaste el límite de 50 consultas por día.',
          UNAUTHORIZED: '🔒 Sesión expirada. Recarga la página.',
          INVALID_SPECIES: '❌ Especie no válida. Selecciona una de la lista.',
          QUESTION_TOO_LONG: '❌ La consulta supera los 2000 caracteres.',
          LLM_UNAVAILABLE: '⏳ El servicio de IA no está disponible. Intenta en 30 segundos.',
        }
        setError(friendly[code] ?? msg)
        setMessages(prev => prev.filter(m => m.id !== assistantMsgId))
        setIsStreaming(false)
        return
      }

      const reader = res.body!.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue
          const raw = line.slice(6).trim()
          if (!raw) continue
          try {
            const parsed = JSON.parse(raw)
            if (parsed.type === 'token') {
              setMessages(prev => prev.map(m =>
                m.id === assistantMsgId ? { ...m, content: m.content + parsed.content } : m
              ))
            } else if (parsed.type === 'done') {
              if (parsed.session_id) setSessionId(parsed.session_id)
              setMessages(prev => prev.map(m =>
                m.id === assistantMsgId
                  ? { ...m, isStreaming: false, sources: parsed.context_sources ?? 0 }
                  : m
              ))
            } else if (parsed.type === 'error') {
              setError(parsed.message ?? 'Error del servidor')
              setMessages(prev => prev.filter(m => m.id !== assistantMsgId))
            }
          } catch { /* chunk incompleto */ }
        }
      }
    } catch (err: unknown) {
      if ((err as Error).name !== 'AbortError') {
        setError('🔌 Sin conexión con el servidor. Verifica que el backend esté corriendo.')
        setMessages(prev => prev.filter(m => m.id !== assistantMsgId))
      }
    } finally {
      setIsStreaming(false)
      abortRef.current = null
    }
  }, [isStreaming, sessionId])

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setMessages(prev => prev.map((m, i) =>
      i === prev.length - 1 ? { ...m, isStreaming: false } : m
    ))
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
    setError(null)
  }, [])

  const loadSession = useCallback(async (sid: string) => {
    try {
      const res = await fetch(`${API_BASE}/chat/history?session_id=${sid}&limit=50`)
      if (!res.ok) return
      const data = await res.json()
      if (!data.success) return
      const loaded: ChatMessage[] = []
      for (const item of data.data) {
        loaded.push({
          id: `${item.id}-q`,
          role: 'user',
          content: item.question,
          species: item.species,
          category: item.category,
          createdAt: new Date(item.created_at),
        })
        loaded.push({
          id: item.id,
          role: 'assistant',
          content: item.answer,
          createdAt: new Date(item.created_at),
          sources: item.sources?.length ?? 0,
        })
      }
      setMessages(loaded)
      setSessionId(sid)
      setError(null)
    } catch { /* silencioso */ }
  }, [])

  return { messages, isStreaming, error, sessionId, sendMessage, stopStreaming, clearMessages, loadSession }
}
