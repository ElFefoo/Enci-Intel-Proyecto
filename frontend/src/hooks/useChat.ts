import { useState, useRef, useCallback } from 'react'
import { streamChatQuery } from '../services/chatService'
import type { ChatMessage, Species } from '../types/chat'
import { v4 as uuidv4 } from 'uuid'

export function useChat() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [sessionId, setSessionId] = useState<string | undefined>()
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = useCallback(async (
    question: string,
    species?: Species,
    category?: string,
  ) => {
    if (!question.trim() || isStreaming) return

    // Agregar mensaje del usuario
    const userMsg: ChatMessage = {
      id: uuidv4(),
      role: 'user',
      content: question.trim(),
      species,
      category,
      createdAt: new Date(),
    }
    setMessages(prev => [...prev, userMsg])

    // Placeholder del asistente con streaming
    const assistantId = uuidv4()
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: 'assistant',
      content: '',
      createdAt: new Date(),
      isStreaming: true,
    }
    setMessages(prev => [...prev, assistantMsg])
    setIsStreaming(true)

    abortRef.current = new AbortController()

    await streamChatQuery(
      { question: question.trim(), species, category, session_id: sessionId },
      (token) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, content: m.content + token } : m
        ))
      },
      (newSessionId) => {
        if (newSessionId) setSessionId(newSessionId)
        setMessages(prev => prev.map(m =>
          m.id === assistantId ? { ...m, isStreaming: false } : m
        ))
        setIsStreaming(false)
      },
      (errorMsg) => {
        setMessages(prev => prev.map(m =>
          m.id === assistantId
            ? { ...m, content: `⚠️ Error: ${errorMsg}`, isStreaming: false }
            : m
        ))
        setIsStreaming(false)
      },
      abortRef.current.signal,
    )
  }, [isStreaming, sessionId])

  const stopStreaming = useCallback(() => {
    abortRef.current?.abort()
    setIsStreaming(false)
    setMessages(prev => prev.map(m =>
      m.isStreaming ? { ...m, isStreaming: false } : m
    ))
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setSessionId(undefined)
  }, [])

  return { messages, isStreaming, sessionId, sendMessage, stopStreaming, clearMessages }
}
