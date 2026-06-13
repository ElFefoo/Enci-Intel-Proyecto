import { useState, useRef, useEffect } from 'react'
import { useChat } from '../hooks/useChat'
import type { Species } from '../types/chat'
import ReactMarkdown from 'react-markdown'

const SPECIES_OPTIONS: { value: Species; label: string }[] = [
  { value: 'bovino', label: '🐄 Bovino' },
  { value: 'porcino', label: '🐷 Porcino' },
  { value: 'aviar', label: '🐔 Aviar' },
  { value: 'canino', label: '🐶 Canino' },
  { value: 'felino', label: '🐱 Felino' },
  { value: 'equino', label: '🐴 Equino' },
]

export default function ConsultorIA() {
  const { messages, isStreaming, sendMessage, stopStreaming, clearMessages } = useChat()
  const [input, setInput] = useState('')
  const [species, setSpecies] = useState<Species | undefined>()
  const [category, setCategory] = useState('')
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
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

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-green-600 flex items-center justify-center text-white font-bold text-sm">
            IA
          </div>
          <div>
            <h1 className="font-semibold text-gray-900">Consultor Veterinario IA</h1>
            <p className="text-xs text-gray-500">Powered by Gemini · Encipharm</p>
          </div>
        </div>
        <button
          onClick={clearMessages}
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          Nueva sesión
        </button>
      </div>

      {/* Filtros */}
      <div className="bg-white border-b border-gray-100 px-6 py-2 flex items-center gap-3">
        <span className="text-xs text-gray-400 font-medium">Filtrar por:</span>
        <select
          value={species ?? ''}
          onChange={e => setSpecies((e.target.value as Species) || undefined)}
          className="text-sm border border-gray-200 rounded-lg px-2 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500"
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
          className="text-sm border border-gray-200 rounded-lg px-3 py-1 text-gray-700 focus:outline-none focus:ring-2 focus:ring-green-500 w-52"
        />
      </div>

      {/* Mensajes */}
      <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center text-3xl mb-4">
              🐄
            </div>
            <h2 className="text-lg font-semibold text-gray-700 mb-2">Consultor Veterinario IA</h2>
            <p className="text-gray-400 text-sm max-w-sm">
              Consulta sobre dosis, protocolos de tratamiento y comparativas de productos veterinarios para el mercado chileno.
            </p>
            <div className="mt-6 grid grid-cols-1 gap-2 w-full max-w-sm">
              {[
                'Dosis de ivermectina para bovinos de 400kg',
                'Comparar enrofloxacina Encipharm vs Zoetis',
                'Protocolo vacunación canina cachorro',
              ].map(suggestion => (
                <button
                  key={suggestion}
                  onClick={() => sendMessage(suggestion, species, category || undefined)}
                  className="text-left text-sm bg-white border border-gray-200 rounded-xl px-4 py-3 hover:border-green-400 hover:bg-green-50 transition-all text-gray-600"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map(msg => (
          <div
            key={msg.id}
            className={`flex ${
              msg.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            {msg.role === 'assistant' && (
              <div className="w-7 h-7 rounded-full bg-green-600 flex items-center justify-center text-white text-xs font-bold mr-2 mt-1 shrink-0">
                IA
              </div>
            )}
            <div
              className={`max-w-2xl rounded-2xl px-4 py-3 text-sm ${
                msg.role === 'user'
                  ? 'bg-green-600 text-white rounded-tr-sm'
                  : 'bg-white border border-gray-200 text-gray-800 rounded-tl-sm shadow-sm'
              }`}
            >
              {msg.role === 'assistant' ? (
                <div className="prose prose-sm max-w-none">
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                  {msg.isStreaming && (
                    <span className="inline-block w-2 h-4 bg-green-500 animate-pulse ml-0.5 rounded-sm" />
                  )}
                </div>
              ) : (
                <p className="whitespace-pre-wrap">{msg.content}</p>
              )}
              {msg.species && (
                <span className="text-xs opacity-60 mt-1 block">
                  {SPECIES_OPTIONS.find(s => s.value === msg.species)?.label}
                </span>
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 px-6 py-4">
        <form onSubmit={handleSubmit} className="flex gap-3 items-end">
          <textarea
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Escribe tu consulta veterinaria... (Enter para enviar)"
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
          Las respuestas son orientativas. Validar siempre con médico veterinario.
        </p>
      </div>
    </div>
  )
}
