import { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { useChat } from '../hooks/useChat'
import type { ChatMessage, Species } from '../types/chat'

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'

const SPECIES_OPTIONS: { value: Species; label: string }[] = [
  { value: 'aves', label: '🐔 Aves' },
  { value: 'porcinos', label: '🐷 Porcinos' },
  { value: 'rumiantes', label: '🐄 Rumiantes' },
  { value: 'peces', label: '🐟 Peces' },
  { value: 'caninos', label: '🐶 Caninos' },
  { value: 'felinos', label: '🐱 Felinos' },
  { value: 'equinos', label: '🐴 Equinos' },
]

const SUGGESTIONS = [
  'Dosis de ivermectina para rumiantes de 400kg',
  'Comparar enrofloxacina Encipharm vs Zoetis en aves',
  'Protocolo vacunación caninos cachorro',
  'Antibióticos permitidos en aves de postura Chile',
]

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  return (
    <button
      onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(() => setCopied(false), 2000) }}
      className="text-xs text-gray-400 hover:text-gray-600 transition-colors px-2 py-1 rounded hover:bg-gray-100"
    >
      {copied ? '✅ Copiado' : '📋 Copiar'}
    </button>
  )
}

function FeedbackButtons({ msgId, onFeedback }: { msgId: string; onFeedback: (id: string, v: 'up' | 'down') => void }) {
  const [voted, setVoted] = useState<'up' | 'down' | null>(null)
  return (
    <div className="flex gap-1">
      {(['up', 'down'] as const).map(v => (
        <button key={v} onClick={() => { setVoted(v); onFeedback(msgId, v) }}
          className={`text-xs px-2 py-1 rounded transition-colors ${
            voted === v
              ? v === 'up' ? 'bg-green-100 text-green-600' : 'bg-red-100 text-red-500'
              : 'text-gray-400 hover:bg-gray-100'
          }`}>
          {v === 'up' ? '👍' : '👎'}
        </button>
      ))}
    </div>
  )
}

function SourcesBadge({ count }: { count: number }) {
  if (!count) return null
  return (
    <span className="text-xs bg-blue-50 text-blue-500 border border-blue-100 rounded-full px-2 py-0.5">
      📚 {count} fuente{count !== 1 ? 's' : ''}
    </span>
  )
}

function ErrorBanner({ message, onClose }: { message: string; onClose: () => void }) {
  return (
    <div className="mx-6 mt-3 bg-red-50 border border-red-200 rounded-xl px-4 py-3 flex items-start gap-3 shrink-0">
      <span className="text-red-600 text-sm flex-1">{message}</span>
      <button onClick={onClose} className="text-red-400 hover:text-red-600 font-bold text-xs">✕</button>
    </div>
  )
}

function MessageBubble({ msg, onFeedback }: { msg: ChatMessage; onFeedback: (id: string, v: 'up' | 'down') => void }) {
  const isUser = msg.role === 'user'
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} group`}>
      {!isUser && (
        <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold mr-2 mt-1 shrink-0">IA</div>
      )}
      <div className="max-w-2xl flex flex-col gap-1">
        <div className={`rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? 'bg-green-600 text-white rounded-tr-sm'
            : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
        }`}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{msg.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-headings:text-gray-800 prose-a:text-green-600 prose-code:bg-gray-100 prose-code:px-1 prose-code:rounded">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
              {msg.isStreaming && <span className="inline-block w-2 h-4 bg-green-500 animate-pulse ml-0.5 rounded-sm" />}
            </div>
          )}
          {msg.species && (
            <span className="text-xs opacity-50 mt-1 block">
              {SPECIES_OPTIONS.find(s => s.value === msg.species)?.label}
            </span>
          )}
        </div>
        {!isUser && !msg.isStreaming && msg.content && (
          <div className="flex items-center gap-2 px-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <CopyButton text={msg.content} />
            <FeedbackButtons msgId={msg.id} onFeedback={onFeedback} />
            {msg.sources !== undefined && <SourcesBadge count={msg.sources} />}
          </div>
        )}
      </div>
    </div>
  )
}

function SessionSidebar({
  sessions, activeId, onSelect, onNew, onDeleteAll,
}: {
  sessions: { id: string; title: string; createdAt: Date; sessionId?: string }[]
  activeId?: string
  onSelect: (id: string, sessionId?: string) => void
  onNew: () => void
  onDeleteAll: () => void
}) {
  return (
    <aside className="w-52 shrink-0 border-r border-gray-200 bg-gray-50 flex flex-col">
      <div className="p-3 border-b border-gray-200">
        <button onClick={onNew}
          className="w-full text-sm bg-green-600 hover:bg-green-700 text-white rounded-xl py-2 font-medium transition-colors">
          + Nueva consulta
        </button>
      </div>
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {sessions.length === 0 && (
          <p className="text-xs text-gray-400 text-center mt-6">Sin historial aún</p>
        )}
        {sessions.map(s => (
          <button key={s.id} onClick={() => onSelect(s.id, s.sessionId)}
            className={`w-full text-left px-3 py-2 rounded-lg text-xs transition-colors ${
              s.id === activeId ? 'bg-green-100 text-green-700 font-medium' : 'text-gray-600 hover:bg-gray-100'
            }`}>
            <p className="truncate font-medium">{s.title}</p>
            <p className="text-gray-400 mt-0.5">
              {s.createdAt.toLocaleDateString('es-CL', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' })}
            </p>
          </button>
        ))}
      </div>
      {sessions.length > 0 && (
        <div className="p-3 border-t border-gray-100">
          <button onClick={onDeleteAll}
            className="w-full text-xs text-red-400 hover:text-red-600 hover:bg-red-50 rounded-lg py-1.5 transition-colors">
            🗑 Borrar historial
          </button>
        </div>
      )}
    </aside>
  )
}

export default function ConsultorIA() {
  const { messages, isStreaming, error, sessionId, sendMessage, stopStreaming, clearMessages, loadSession } = useChat()
  const [input, setInput] = useState('')
  const [species, setSpecies] = useState<Species | undefined>()
  const [category, setCategory] = useState('')
  const [sessions, setSessions] = useState<{ id: string; title: string; createdAt: Date; sessionId?: string }[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | undefined>()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'user') {
      const s = {
        id: crypto.randomUUID(),
        title: messages[0].content.slice(0, 45) + (messages[0].content.length > 45 ? '...' : ''),
        createdAt: new Date(),
        sessionId,
      }
      setSessions(prev => [s, ...prev])
      setActiveSessionId(s.id)
    }
  }, [messages, sessionId])

  useEffect(() => {
    if (sessionId && activeSessionId) {
      setSessions(prev => prev.map(s =>
        s.id === activeSessionId ? { ...s, sessionId } : s
      ))
    }
  }, [sessionId, activeSessionId])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isStreaming || input.length > 2000) return
    sendMessage(input.trim(), species, category || undefined)
    setInput('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e as unknown as React.FormEvent) }
  }

  const handleSelectSession = async (localId: string, sid?: string) => {
    setActiveSessionId(localId)
    if (sid) await loadSession(sid)
    else clearMessages()
  }

  const handleDeleteAll = async () => {
    if (!confirm('¿Eliminar todo el historial? Esta acción es irreversible.')) return
    try {
      await fetch(`${API_BASE}/chat/history`, { method: 'DELETE' })
    } catch { /* silencioso */ }
    setSessions([])
    clearMessages()
    setActiveSessionId(undefined)
  }

  const handleFeedback = useCallback((msgId: string, vote: 'up' | 'down') => {
    console.info(`feedback msg=${msgId} vote=${vote}`)
  }, [])

  const handleExport = () => {
    if (!messages.length) return
    const lines = messages.map(m => `[${m.role === 'user' ? 'Usuario' : 'Consultor IA'}]\n${m.content}`)
    const blob = new Blob([lines.join('\n\n---\n\n')], { type: 'text/plain;charset=utf-8' })
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(blob),
      download: `consulta-enci-intel-${new Date().toISOString().slice(0, 10)}.txt`,
    })
    a.click()
    URL.revokeObjectURL(a.href)
  }

  const charCount = input.length

  return (
    <div className="flex h-full">
      <SessionSidebar
        sessions={sessions}
        activeId={activeSessionId}
        onSelect={handleSelectSession}
        onNew={() => { clearMessages(); setActiveSessionId(undefined) }}
        onDeleteAll={handleDeleteAll}
      />

      <div className="flex flex-col flex-1 min-w-0">
        <div className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-green-600 flex items-center justify-center text-white font-bold text-xs">IA</div>
            <div>
              <h1 className="font-semibold text-gray-900 text-sm">Consultor Veterinario IA</h1>
              <p className="text-xs text-gray-400">Powered by Groq · Encipharm</p>
            </div>
          </div>
          {messages.length > 0 && (
            <button onClick={handleExport}
              className="text-xs text-gray-400 hover:text-gray-600 border border-gray-200 rounded-lg px-3 py-1.5 hover:bg-gray-50 transition-colors">
              ⬇️ Exportar
            </button>
          )}
        </div>

        <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-3 shrink-0">
          <span className="text-xs text-gray-400 font-medium">Filtrar:</span>
          <select value={species ?? ''} onChange={e => setSpecies((e.target.value as Species) || undefined)}
            className="text-xs border border-gray-200 rounded-lg px-2 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500">
            <option value="">Todas las especies</option>
            {SPECIES_OPTIONS.map(s => <option key={s.value} value={s.value}>{s.label}</option>)}
          </select>
          <input type="text" placeholder="Categoría (ej: antiparasitario)" value={category}
            onChange={e => setCategory(e.target.value)}
            className="text-xs border border-gray-200 rounded-lg px-3 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500 w-48" />
        </div>

        {error && <ErrorBanner message={error} onClose={() => {}} />}

        <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
          {messages.length === 0 && !error && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center text-3xl mb-4">🐄</div>
              <h2 className="text-lg font-semibold text-gray-700 mb-1">Consultor Veterinario IA</h2>
              <p className="text-gray-400 text-sm max-w-sm mb-6">Consultas técnicas sobre dosis, protocolos y comparativas de productos para el mercado chileno.</p>
              <div className="grid grid-cols-1 gap-2 w-full max-w-md">
                {SUGGESTIONS.map(s => (
                  <button key={s} onClick={() => sendMessage(s, species, category || undefined)}
                    className="text-left text-sm bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-green-400 hover:bg-green-50 transition-all text-gray-600">
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}
          {messages.map(msg => <MessageBubble key={msg.id} msg={msg} onFeedback={handleFeedback} />)}
          <div ref={bottomRef} />
        </div>

        <div className="bg-white border-t border-gray-200 px-6 py-4 shrink-0">
          <form onSubmit={handleSubmit} className="flex gap-3 items-end">
            <div className="flex-1 relative">
              <textarea value={input} onChange={e => setInput(e.target.value)} onKeyDown={handleKeyDown}
                placeholder="Escribe tu consulta veterinaria... (Enter para enviar, Shift+Enter nueva línea)"
                rows={1} disabled={isStreaming} maxLength={2000}
                className={`w-full resize-none border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 disabled:bg-gray-50 disabled:text-gray-400 max-h-32 overflow-y-auto ${
                  charCount > 1800 ? 'border-orange-300' : 'border-gray-200'
                }`}
                style={{ minHeight: '44px' }} />
              {charCount > 1800 && (
                <span className="absolute bottom-2 right-3 text-xs text-orange-400">{charCount}/2000</span>
              )}
            </div>
            {isStreaming ? (
              <button type="button" onClick={stopStreaming}
                className="px-4 py-3 bg-red-500 hover:bg-red-600 text-white rounded-xl text-sm font-medium transition-colors shrink-0">
                ⏹ Detener
              </button>
            ) : (
              <button type="submit" disabled={!input.trim() || charCount > 2000}
                className="px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-200 disabled:text-gray-400 text-white rounded-xl text-sm font-medium transition-colors shrink-0">
                Enviar ↑
              </button>
            )}
          </form>
          <p className="text-xs text-gray-400 mt-2 text-center">Respuestas orientativas. Validar siempre con médico veterinario.</p>
        </div>
      </div>
    </div>
  )
}
