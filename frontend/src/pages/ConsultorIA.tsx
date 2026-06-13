import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChat } from '../hooks/useChat'
import type { ChatMessage, Species } from '../types/chat'

const SPECIES_OPTIONS: { value: Species; label: string }[] = [
  { value: 'bovino', label: '🐄 Bovino' },
  { value: 'porcino', label: '🐷 Porcino' },
  { value: 'aviar', label: '🐔 Aviar' },
  { value: 'canino', label: '🐶 Canino' },
  { value: 'felino', label: '🐱 Felino' },
  { value: 'equino', label: '🐴 Equino' },
]

const SUGGESTIONS = [
  'Dosis de ivermectina para bovinos de 400kg',
  'Comparar enrofloxacina Encipharm vs Zoetis',
  'Protocolo vacunación canina cachorro',
  'Antibióticos permitidos en aves de postura Chile',
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const handle = () => {
    navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <button
      onClick={handle}
      className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-2 py-1 rounded hover:bg-gray-100"
      title="Copiar respuesta"
    >
      {copied ? '✅ Copiado' : '📋 Copiar'}
    </button>
  )
}

function FeedbackButtons({ msgId, onFeedback }: { msgId: string; onFeedback: (id: string, v: 'up' | 'down') => void }) {
  const [voted, setVoted] = useState<'up' | 'down' | null>(null)
  const vote = (v: 'up' | 'down') => {
    setVoted(v)
    onFeedback(msgId, v)
  }
  return (
    <div className="flex gap-1">
      <button
        onClick={() => vote('up')}
        className={`text-xs px-2 py-1 rounded transition-colors ${
          voted === 'up' ? 'bg-green-100 text-green-600' : 'text-gray-400 hover:bg-gray-100'
        }`}
        title="Útil"
      >
        👍
      </button>
      <button
        onClick={() => vote('down')}
        className={`text-xs px-2 py-1 rounded transition-colors ${
          voted === 'down' ? 'bg-red-100 text-red-500' : 'text-gray-400 hover:bg-gray-100'
        }`}
        title="No útil"
      >
        👎
      </button>
    </div>
  )
}

function MessageBubble({
  msg,
  onFeedback,
}: {
  msg: ChatMessage
  onFeedback: (id: string, v: 'up' | 'down') => void
}) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold mr-2 mt-1 shrink-0">
          IA
        </div>
      )}
      <div className="max-w-2xl flex flex-col gap-1">
        <div
          className={`rounded-2xl px-4 py-3 text-sm ${
            isUser
              ? 'bg-green-600 text-white rounded-tr-sm'
              : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-a:text-green-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded prose-table:text-xs">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {msg.content}
              </ReactMarkdown>
              {msg.isStreaming && (
                <span className="inline-block w-2 h-4 bg-green-500 animate-pulse ml-0.5 rounded-sm" />
              )}
            </div>
          )}
          {msg.species && (
            <span className="text-xs opacity-50 mt-1 block">
              {SPECIES_OPTIONS.find(s => s.value === msg.species)?.label}
            </span>
          )}
        </div>
        {!isUser && !msg.isStreaming && msg.content && (
          <div className="flex items-center gap-1 px-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <CopyButton text={msg.content} />
            <FeedbackButtons msgId={msg.id} onFeedback={onFeedback} />
          </div>
        )}
      </div>
    </div>
  )
}

function SessionSidebar({
  sessions,
  activeId,
  onSelect,
  onNew,
}: {
  sessions: { id: string; title: string; createdAt: Date }[]
  activeId?: string
  onSelect: (id: string) => void
  onNew: () => void
}) {
  return (
    <aside className="w-56 shrink-0 border-r border-gray-200 bg-gray-50 flex flex-col">
      <div className="p-3 border-b border-gray-200">
        <button
          onClick={onNew}
          className="w-full text-sm bg-green-600 hover:bg-green-700 text-white rounded-xl py-2 font-medium transition-colors"
        >
          + Nueva consulta
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-4">Sin historial aún</p>
        )}
        {sessions.map(s => (
          <button
            key={s.id}
            onClick={() => onSelect(s.id)}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
              s.id === activeId
                ? 'bg-green-100 text-green-700 font-medium'
                : 'text-gray-600 hover:bg-gray-100'
            }`}
          >
            <p className="truncate font-medium">{s.title}</p>
            <p className="text-gray-400 mt-0.5">
              {s.createdAt.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
            </p>
          </button>
        ))}
      </div>
    </aside>
  )
}

export default function ConsultorIA() {
  const { messages, isStreaming, sendMessage, stopStreaming, clearMessages } = useChat()
  const [input, setInput] = useState('')
  const [species, setSpecies] = useState<Species | undefined>()
  const [category, setCategory] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  // Historial de sesiones (local en memoria)
  const [sessions, setSessions] = useState<{ id: string; title: string; createdAt: Date }[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Guardar sesión al primer mensaje
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'user') {
      const newSession = {
        id: crypto.randomUUID(),
        title: messages[0].content.slice(0, 40) + (messages[0].content.length > 40 ? '...' : ''),
        createdAt: new Date(),
      }
      setSessions(prev => [newSession, ...prev])
      setActiveSessionId(newSession.id)
    }
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming) return
    sendMessage(input.trim(), species, category || undefined)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  const handleNewSession = () => {
    clearMessages()
    setActiveSessionId(undefined)
    setInput('')
  }

  const handleFeedback = useCallback((msgId: string, vote: 'up' | 'down') => {
    console.info(`Feedback msg=${msgId} vote=${vote}`)
    // TODO: enviar al backend cuando exista el endpoint
  }, [])

  const handleExport = () => {
    if (messages.length === 0) return
    const lines = messages.map(m =>
      `[${m.role === 'user' ? 'Usuario' : 'Consultor IA'}]\n${m.content}\n`
    )
    const blob = new Blob([lines.join('\n---\n\n')], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `consulta-enci-intel-${new Date().toISOString().slice(0, 10)}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="flex h-full">
      {/* Sidebar historial */}
      <SessionSidebar
        sessions={sessions}
        activeId={activeSessionId}
        onSelect={setActiveSessionId}
        onNew={handleNewSession}
      />

      {/* Chat principal */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white font-bold text-xs">
              IA
            </div>
            <div>
              <h1 className="font-semibold text-gray-900 text-sm">Consultor Veterinario IA</h1>
              <p className="text-xs text-gray-400">Powered by Gemini · Encipharm</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={handleExport}
                className="text-xs text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors"
              >
                ⬇️ Exportar
              </button>
            )}
          </div>
        </div>

        {/* Filtros */}
        <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-3 shrink-0">
          <span className="text-xs text-gray-400 font-medium">Filtrar:</span>
          <select
            value={species ?? ''}
            onChange={e => setSpecies((e.target.value as Species) || undefined)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500"
          >
            <option value="">Todas las especies</option>
            {SPECIES_OPTIONS.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          <input
            type="text"
            placeholder="Categoría (ej: antiparasitario)"
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500 w-48"
          />
        </div>

        {/* Mensajes */}
        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center text-3xl mb-4">
                🐄
              </div>
              <h2 className="text-lg font-semibold text-gray-700 mb-1">Consultor Veterinario IA</h2>
              <p className="text-gray-400 text-sm max-w-sm mb-6">
                Consultas técnicas sobre dosis, protocolos y comparativas de productos para el mercado chileno.
              </p>
              <div className="grid grid-cols-1 gap-2 w-full max-w-md">
                {SUGGESTIONS.map(s => (
                  <button
                    key={s}
                    onClick={() => sendMessage(s, species, category || undefined)}
                    className="text-left text-sm bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-green-400 hover:bg-green-50 transition-all text-gray-600"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map(msg => (
            <MessageBubble key={msg.id} msg={msg} onFeedback={handleFeedback} />
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input */}
        <div className="bg-white border-t border-gray-200 px-6 py-4 shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <textarea
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribe tu consulta veterinaria... (Enter para enviar, Shift+Enter nueva línea)"
              rows={1}
              disabled={isStreaming}
              className="flex-1 resize-none border border-gray-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-50 disabled:text-gray-400 max-h-32 overflow-y-auto"
              style={{ minHeight: '44px' }}
            />
            {isStreaming ? (
              <button
                type="button"
                onClick={stopStreaming}
                className="px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors shrink-0"
              >
                ⏹ Detener
              </button>
            ) : (
              <button
                type="submit"
                disabled={!input.trim()}
                className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-200 disabled:text-gray-400 text-white rounded-xl text-sm font-medium transition-colors shrink-0"
              >
                Enviar ↑
              </button>
            )}
          </form>
          <p className="text-xs text-gray-400 mt-2 text-center">
            Respuestas orientativas. Validar siempre con médico veterinario.
          </p>
        </div>
      </div>
    </div>
  )
}
