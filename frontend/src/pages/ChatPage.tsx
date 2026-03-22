import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Send, ThumbsUp, ThumbsDown, Copy, FileText,
  ChevronRight, Plus, Loader2, FolderOpen, ChevronDown,
  Download, RefreshCw, X,
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DOMPurify from 'dompurify'
import { askApi, feedbackApi, collectionsApi } from '../api'
import { useUIStore } from '../store/uiStore'
import type { ChatMessage, Citation } from '../types'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const queryClient = useQueryClient()
  const { currentSessionId, setCurrentSessionId, currentCollectionId, setCurrentCollectionId } = useUIStore()
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const [collectionDropdownOpen, setCollectionDropdownOpen] = useState(false)
  const [regeneratingId, setRegeneratingId] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  const { data: collectionsData } = useQuery({ queryKey: ['collections'], queryFn: () => collectionsApi.list() })
  const { data: historyData } = useQuery({
    queryKey: ['chatHistory', currentSessionId],
    queryFn: () => askApi.getHistory(currentSessionId || undefined),
    enabled: !!currentSessionId,
  })
  const { data: sessionsData } = useQuery({ queryKey: ['chatSessions'], queryFn: () => askApi.getSessions() })

  useEffect(() => { if (historyData?.messages) setMessages(historyData.messages) }, [historyData])
  useEffect(() => { messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  const currentCollection = collectionsData?.collections.find(c => c.id === currentCollectionId)

  const askMutation = useMutation({
    mutationFn: (q: string) => askApi.ask({
      question: q,
      session_id: currentSessionId || undefined,
      collection_id: currentCollectionId || undefined,
      top_k: 5, alpha: 0.7,
    }),
    onMutate: (q) => {
      setMessages(prev => [...prev, {
        id: 'temp-' + Date.now(), question: q, answer: '',
        citations: [], feedback: null, created_at: new Date().toISOString(), isLoading: true,
      }])
    },
    onSuccess: (response) => {
      if (!currentSessionId) setCurrentSessionId(response.session_id)
      setMessages(prev => [
        ...prev.filter(m => !m.id.startsWith('temp-')),
        { id: response.qa_id, question: question, answer: response.answer,
          citations: response.citations, feedback: null, created_at: new Date().toISOString() },
      ])
      queryClient.invalidateQueries({ queryKey: ['chatHistory'] })
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
    onError: () => {
      setMessages(prev => prev.filter(m => !m.id.startsWith('temp-')))
      toast.error('Failed to get answer')
    },
  })

  const feedbackMutation = useMutation({
    mutationFn: ({ qaId, thumb }: { qaId: string; thumb: 'up' | 'down' }) =>
      feedbackApi.submit({ qa_id: qaId, thumb }),
    onSuccess: () => toast.success('Feedback saved'),
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || askMutation.isPending) return
    askMutation.mutate(question)
    setQuestion('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSubmit(e) }
  }

  const startNewChat = () => { setCurrentSessionId(null); setMessages([]); setQuestion(''); inputRef.current?.focus() }

  const copyToClipboard = (text: string) => { navigator.clipboard.writeText(text); toast.success('Copied') }

  const regenerateAnswer = async (msg: ChatMessage) => {
    setRegeneratingId(msg.id)
    try {
      const response = await askApi.ask({
        question: msg.question,
        session_id: currentSessionId || undefined,
        collection_id: currentCollectionId || undefined,
        top_k: 5, alpha: 0.7,
      })
      setMessages(prev => prev.map(m => m.id === msg.id
        ? { ...m, answer: response.answer, citations: response.citations } : m))
      toast.success('Regenerated')
    } catch { toast.error('Failed to regenerate') }
    finally { setRegeneratingId(null) }
  }

  const exportSession = async (sessionId: string, title: string) => {
    try {
      const history = await askApi.getHistory(sessionId, 100)
      if (!history.messages.length) { toast.error('No messages to export'); return }
      const lines = [
        `# ${title}`, `Session: ${sessionId}`,
        `Collection: ${currentCollection?.name || 'All Documents'}`,
        `Exported: ${new Date().toLocaleString()}`, '', '---', '',
      ]
      history.messages.forEach((msg, idx) => {
        lines.push(`## Q${idx + 1}: ${msg.question}`, '', msg.answer, '')
        if (msg.citations.length > 0) {
          lines.push('**Sources:**')
          msg.citations.forEach(c => lines.push(`- ${c.document_name}${c.page_number ? ` (p.${c.page_number})` : ''}`))
          lines.push('')
        }
        lines.push('---', '')
      })
      const blob = new Blob([lines.join('\n')], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `chat-${title.slice(0, 30).replace(/\s+/g, '-')}-${sessionId.slice(0, 8)}.md`
      a.click()
      URL.revokeObjectURL(url)
      toast.success('Exported')
    } catch { toast.error('Export failed') }
  }

  return (
    <div className="flex h-full overflow-hidden">
      {/* ── Sessions sidebar ── */}
      <div className="w-56 flex-shrink-0 flex flex-col overflow-hidden"
        style={{ background: '#000', borderRight: '1px solid #1a1a1a' }}>

        {/* Collection picker */}
        <div className="p-2 flex-shrink-0" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <div className="relative">
            <button
              onClick={() => setCollectionDropdownOpen(!collectionDropdownOpen)}
              className="w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-xs transition-colors"
              style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', color: '#888' }}
            >
              <FolderOpen size={12} className="flex-shrink-0" style={{ color: '#555' }} />
              <span className="flex-1 truncate text-left">{currentCollection?.name || 'All Documents'}</span>
              <ChevronDown size={11} style={{ color: '#555' }} />
            </button>
            {collectionDropdownOpen && (
              <div className="absolute top-full left-0 right-0 mt-1 rounded-lg py-1 z-10 animate-fade-in"
                style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', boxShadow: '0 10px 30px rgba(0,0,0,0.8)' }}>
                <button
                  onClick={() => { setCurrentCollectionId(null); setCollectionDropdownOpen(false); startNewChat() }}
                  className="w-full text-left px-3 py-1.5 text-xs transition-colors"
                  style={{ color: !currentCollectionId ? '#fff' : '#888' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#111')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  All Documents
                </button>
                {collectionsData?.collections.map(c => (
                  <button key={c.id}
                    onClick={() => { setCurrentCollectionId(c.id); setCollectionDropdownOpen(false); startNewChat() }}
                    className="w-full text-left px-3 py-1.5 text-xs transition-colors"
                    style={{ color: currentCollectionId === c.id ? '#fff' : '#888' }}
                    onMouseEnter={e => (e.currentTarget.style.background = '#111')}
                    onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                  >
                    <span className="block truncate">{c.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          <button onClick={startNewChat}
            className="btn btn-secondary w-full mt-2 py-2 text-xs">
            <Plus size={12} /> New chat
          </button>
        </div>

        {/* Session list */}
        <div className="flex-1 overflow-y-auto py-1">
          {sessionsData?.sessions.map(session => (
            <div key={session.session_id} className="flex items-center gap-1 px-1.5 py-0.5">
              <button
                onClick={() => setCurrentSessionId(session.session_id)}
                className="flex-1 text-left px-2 py-2 rounded-lg text-xs transition-colors min-w-0"
                style={{
                  background: currentSessionId === session.session_id ? '#111' : 'transparent',
                  color: currentSessionId === session.session_id ? '#fff' : '#555',
                }}
                onMouseEnter={e => { if (currentSessionId !== session.session_id) e.currentTarget.style.background = '#0a0a0a' }}
                onMouseLeave={e => { if (currentSessionId !== session.session_id) e.currentTarget.style.background = 'transparent' }}
              >
                <p className="truncate font-medium">{session.title}</p>
                <p className="mt-0.5" style={{ color: '#333', fontSize: 10 }}>
                  {new Date(session.last_activity).toLocaleDateString()}
                </p>
              </button>
              <button onClick={() => exportSession(session.session_id, session.title)}
                className="btn-ghost p-1.5 flex-shrink-0" title="Export">
                <Download size={11} />
              </button>
            </div>
          ))}
          {(!sessionsData?.sessions?.length) && (
            <p className="px-4 py-6 text-xs text-center" style={{ color: '#333' }}>No sessions yet</p>
          )}
        </div>
      </div>

      {/* ── Chat area ── */}
      <div className="flex-1 flex flex-col overflow-hidden" style={{ background: '#000' }}>
        {/* Collection banner */}
        {currentCollectionId && currentCollection && (
          <div className="flex items-center gap-2 px-5 py-2 flex-shrink-0"
            style={{ background: '#0a0a0a', borderBottom: '1px solid #1a1a1a' }}>
            <FolderOpen size={12} style={{ color: '#555' }} />
            <span className="text-xs" style={{ color: '#555' }}>
              Searching in <span style={{ color: '#888' }}>{currentCollection.name}</span>
            </span>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-5 py-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center animate-fade-up">
              <div className="w-12 h-12 rounded-2xl flex items-center justify-center mb-5"
                style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
                <FileText size={20} style={{ color: '#555' }} />
              </div>
              <h3 className="text-base font-semibold mb-2" style={{ color: '#fff' }}>
                Ask InsightForge
              </h3>
              <p className="text-sm max-w-xs" style={{ color: '#555' }}>
                {currentCollectionId
                  ? `Searching in "${currentCollection?.name}"`
                  : 'Ask anything about your documents.'}
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="space-y-3 animate-fade-in">
                {/* User */}
                <div className="flex justify-end">
                  <div className="bubble-user max-w-xl">{message.question}</div>
                </div>

                {/* Assistant */}
                <div className="flex justify-start">
                  <div className="bubble-assistant max-w-2xl w-full">
                    {message.isLoading ? (
                      <div className="flex items-center gap-2" style={{ color: '#555' }}>
                        <Loader2 size={13} className="animate-spin" />
                        <span className="text-xs">Searching...</span>
                      </div>
                    ) : (
                      <>
                        <div className="markdown-content">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {DOMPurify.sanitize(message.answer)}
                          </ReactMarkdown>
                        </div>

                        {/* Citations */}
                        {message.citations.length > 0 && (
                          <div className="mt-3 pt-3" style={{ borderTop: '1px solid #1a1a1a' }}>
                            <p className="text-xs mb-2" style={{ color: '#333' }}>Sources</p>
                            <div className="flex flex-wrap gap-1.5">
                              {message.citations.map((citation, idx) => (
                                <button key={idx} onClick={() => setSelectedCitation(citation)}
                                  className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs transition-colors"
                                  style={{ background: '#111', border: '1px solid #1a1a1a', color: '#888' }}
                                  onMouseEnter={e => { e.currentTarget.style.background = '#1a1a1a'; e.currentTarget.style.color = '#fff' }}
                                  onMouseLeave={e => { e.currentTarget.style.background = '#111'; e.currentTarget.style.color = '#888' }}
                                >
                                  <FileText size={10} />
                                  {citation.document_name}{citation.page_number && ` · p${citation.page_number}`}
                                  <ChevronRight size={10} />
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="mt-3 flex items-center gap-1" style={{ borderTop: '1px solid #1a1a1a', paddingTop: 10 }}>
                          <button onClick={() => copyToClipboard(message.answer)} className="btn-ghost py-1 px-2 text-xs gap-1.5" title="Copy">
                            <Copy size={12} />
                          </button>
                          <button onClick={() => regenerateAnswer(message)} disabled={regeneratingId === message.id}
                            className="btn-ghost py-1 px-2 text-xs" title="Regenerate">
                            <RefreshCw size={12} className={regeneratingId === message.id ? 'animate-spin' : ''} />
                          </button>
                          <div className="flex items-center gap-0.5 ml-1">
                            <button
                              onClick={() => feedbackMutation.mutate({ qaId: message.id, thumb: 'up' })}
                              disabled={message.feedback !== null}
                              className="btn-ghost py-1 px-2"
                              style={{ color: message.feedback === 'up' ? '#4ade80' : '#555' }}
                            >
                              <ThumbsUp size={12} />
                            </button>
                            <button
                              onClick={() => feedbackMutation.mutate({ qaId: message.id, thumb: 'down' })}
                              disabled={message.feedback !== null}
                              className="btn-ghost py-1 px-2"
                              style={{ color: message.feedback === 'down' ? '#f87171' : '#555' }}
                            >
                              <ThumbsDown size={12} />
                            </button>
                          </div>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="flex-shrink-0 px-5 pb-5 pt-3" style={{ borderTop: '1px solid #1a1a1a' }}>
          <form onSubmit={handleSubmit}
            className="flex items-end gap-3 rounded-xl p-3"
            style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
            <textarea
              ref={inputRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={currentCollectionId ? `Ask about "${currentCollection?.name}"…` : 'Ask a question…'}
              rows={1}
              style={{
                background: 'transparent', border: 'none', outline: 'none',
                resize: 'none', flex: 1, color: '#fff', fontSize: 14,
                fontFamily: 'inherit', lineHeight: 1.5,
                maxHeight: 120, overflowY: 'auto',
              }}
              onInput={e => {
                const t = e.currentTarget
                t.style.height = 'auto'
                t.style.height = Math.min(t.scrollHeight, 120) + 'px'
              }}
            />
            <button type="submit" disabled={!question.trim() || askMutation.isPending}
              className="btn btn-primary flex-shrink-0 p-2.5 rounded-lg">
              {askMutation.isPending
                ? <Loader2 size={14} className="animate-spin" />
                : <Send size={14} />
              }
            </button>
          </form>
          <p className="text-center mt-2 text-xs" style={{ color: '#333' }}>
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>

      {/* ── Citation panel ── */}
      {selectedCitation && (
        <div className="w-72 flex-shrink-0 flex flex-col overflow-hidden animate-slide-in"
          style={{ background: '#000', borderLeft: '1px solid #1a1a1a' }}>
          <div className="flex items-center justify-between px-4 py-3 flex-shrink-0"
            style={{ borderBottom: '1px solid #1a1a1a' }}>
            <span className="text-xs font-medium" style={{ color: '#888' }}>Source</span>
            <button onClick={() => setSelectedCitation(null)} className="btn-ghost p-1">
              <X size={13} />
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            <div>
              <p className="text-xs mb-1" style={{ color: '#555' }}>Document</p>
              <p className="text-sm font-medium" style={{ color: '#fff' }}>{selectedCitation.document_name}</p>
            </div>
            {selectedCitation.page_number && (
              <div>
                <p className="text-xs mb-1" style={{ color: '#555' }}>Page</p>
                <p className="text-sm font-mono" style={{ color: '#888' }}>{selectedCitation.page_number}</p>
              </div>
            )}
            <div>
              <p className="text-xs mb-1" style={{ color: '#555' }}>Relevance</p>
              <div className="flex items-center gap-2">
                <div className="flex-1 rounded-full h-1" style={{ background: '#1a1a1a' }}>
                  <div className="h-1 rounded-full" style={{
                    width: `${Math.min(selectedCitation.relevance_score * 100, 100)}%`,
                    background: '#fff',
                  }} />
                </div>
                <span className="text-xs font-mono" style={{ color: '#555' }}>
                  {(selectedCitation.relevance_score * 100).toFixed(0)}%
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs mb-1.5" style={{ color: '#555' }}>Excerpt</p>
              <p className="text-xs leading-relaxed p-3 rounded-lg" style={{
                background: '#0a0a0a', border: '1px solid #1a1a1a', color: '#888',
              }}>
                {selectedCitation.text_snippet}
              </p>
            </div>
          </div>
        </div>
      )}

      {collectionDropdownOpen && (
        <div className="fixed inset-0 z-0" onClick={() => setCollectionDropdownOpen(false)} />
      )}
    </div>
  )
}