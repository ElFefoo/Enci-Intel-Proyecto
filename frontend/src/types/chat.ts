// Species alineados con la spec del API
export type Species =
  | 'aves'
  | 'porcinos'
  | 'rumiantes'
  | 'peces'
  | 'caninos'
  | 'felinos'
  | 'equinos'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  species?: Species
  category?: string
  createdAt: Date
  isStreaming?: boolean
  sources?: number
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
  message_id?: string
  context_sources?: number
  sources?: { title: string; type: string }[]
  message?: string
}
