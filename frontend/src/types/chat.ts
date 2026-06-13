export type Species = 'bovino' | 'porcino' | 'aviar' | 'canino' | 'felino' | 'equino'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  species?: Species
  category?: string
  createdAt: Date
  isStreaming?: boolean
}

export interface ChatSession {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  messageCount: number
}

export interface ChatQueryRequest {
  question: string
  species?: Species
  category?: string
  session_id?: string
}

export interface SSEToken {
  type: 'token' | 'done' | 'error'
  content?: string
  session_id?: string
  context_sources?: number
  message?: string
}
