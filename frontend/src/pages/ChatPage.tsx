import { useState, useRef, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Send, ThumbsUp, ThumbsDown, Copy, Clock, FileText, ChevronRight, Plus, Loader2 } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import DOMPurify from 'dompurify'
import { askApi, feedbackApi } from '../api'
import { useUIStore } from '../store/uiStore'
import type { ChatMessage, Citation } from '../types'
import toast from 'react-hot-toast'

export default function ChatPage() {
  const queryClient = useQueryClient()
  const { currentSessionId, setCurrentSessionId } = useUIStore()
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [selectedCitation, setSelectedCitation] = useState<Citation | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Fetch chat history
  const { data: historyData } = useQuery({
    queryKey: ['chatHistory', currentSessionId],
    queryFn: () => askApi.getHistory(currentSessionId || undefined),
    enabled: !!currentSessionId,
  })

  // Fetch sessions
  const { data: sessionsData } = useQuery({
    queryKey: ['chatSessions'],
    queryFn: () => askApi.getSessions(),
  })

  // Update messages when history is fetched
  useEffect(() => {
    if (historyData?.messages) {
      setMessages(historyData.messages)
    }
  }, [historyData])

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Ask mutation
  const askMutation = useMutation({
    mutationFn: (q: string) =>
      askApi.ask({
        question: q,
        session_id: currentSessionId || undefined,
        top_k: 5,
        alpha: 0.7,
      }),
    onMutate: (q) => {
      // Add user message immediately
      const tempMessage: ChatMessage = {
        id: 'temp-' + Date.now(),
        question: q,
        answer: '',
        citations: [],
        feedback: null,
        created_at: new Date().toISOString(),
        isLoading: true,
      }
      setMessages((prev) => [...prev, tempMessage])
    },
    onSuccess: (response) => {
      // Update session ID
      if (!currentSessionId) {
        setCurrentSessionId(response.session_id)
      }

      // Replace temp message with real one
      setMessages((prev) => {
        const filtered = prev.filter((m) => !m.id.startsWith('temp-'))
        return [
          ...filtered,
          {
            id: response.qa_id,
            question: question,
            answer: response.answer,
            citations: response.citations,
            feedback: null,
            created_at: new Date().toISOString(),
          },
        ]
      })

      // Invalidate queries
      queryClient.invalidateQueries({ queryKey: ['chatHistory'] })
      queryClient.invalidateQueries({ queryKey: ['chatSessions'] })
    },
    onError: () => {
      // Remove temp message
      setMessages((prev) => prev.filter((m) => !m.id.startsWith('temp-')))
      toast.error('Failed to get answer. Please try again.')
    },
  })

  // Feedback mutation
  const feedbackMutation = useMutation({
    mutationFn: ({ qaId, thumb }: { qaId: string; thumb: 'up' | 'down' }) =>
      feedbackApi.submit({ qa_id: qaId, thumb }),
    onSuccess: () => {
      toast.success('Thank you for your feedback!')
    },
  })

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!question.trim() || askMutation.isPending) return

    askMutation.mutate(question)
    setQuestion('')
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  const startNewChat = () => {
    setCurrentSessionId(null)
    setMessages([])
    setQuestion('')
    inputRef.current?.focus()
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Copied to clipboard')
  }

  return (
    <div className="flex h-[calc(100vh-8rem)] gap-4">
      {/* Sessions sidebar */}
      <div className="w-64 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 bg-primary-600 hover:bg-primary-700 text-white py-2 px-4 rounded-lg transition-colors"
          >
            <Plus size={18} />
            New Chat
          </button>
        </div>
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          {sessionsData?.sessions.map((session) => (
            <button
              key={session.session_id}
              onClick={() => setCurrentSessionId(session.session_id)}
              className={`w-full text-left p-3 rounded-lg transition-colors ${
                currentSessionId === session.session_id
                  ? 'bg-primary-50 dark:bg-primary-900/20 text-primary-600 dark:text-primary-400'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <p className="text-sm font-medium truncate">{session.title}</p>
              <p className="text-xs text-gray-500 mt-1 flex items-center gap-1">
                <Clock size={12} />
                {new Date(session.last_activity).toLocaleDateString()}
              </p>
            </button>
          ))}
          {(!sessionsData?.sessions || sessionsData.sessions.length === 0) && (
            <p className="text-sm text-gray-500 text-center py-4">
              No chat history yet
            </p>
          )}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex-1 flex flex-col bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center">
              <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center mb-4">
                <FileText className="text-primary-600 dark:text-primary-400" size={32} />
              </div>
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                Ask a Question
              </h3>
              <p className="text-gray-600 dark:text-gray-400 max-w-md">
                Ask questions about your internal documents. I'll search through uploaded
                files and provide answers with exact citations.
              </p>
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="space-y-4 animate-fade-in">
                {/* User message */}
                <div className="flex justify-end">
                  <div className="chat-bubble-user max-w-2xl">
                    <p>{message.question}</p>
                  </div>
                </div>

                {/* Assistant message */}
                <div className="flex justify-start">
                  <div className="chat-bubble-assistant max-w-3xl">
                    {message.isLoading ? (
                      <div className="flex items-center gap-2 text-gray-500">
                        <Loader2 className="animate-spin" size={16} />
                        <span>Searching documents and generating answer...</span>
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
                          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <p className="text-xs font-medium text-gray-500 mb-2">Sources:</p>
                            <div className="flex flex-wrap gap-2">
                              {message.citations.map((citation, idx) => (
                                <button
                                  key={idx}
                                  onClick={() => setSelectedCitation(citation)}
                                  className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 dark:bg-gray-700 rounded text-xs text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                                >
                                  <FileText size={12} />
                                  {citation.document_name}
                                  {citation.page_number && ` (p.${citation.page_number})`}
                                  <ChevronRight size={12} />
                                </button>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Actions */}
                        <div className="mt-4 flex items-center gap-2">
                          <button
                            onClick={() => copyToClipboard(message.answer)}
                            className="p-1.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
                            title="Copy answer"
                          >
                            <Copy size={14} />
                          </button>
                          <div className="flex items-center gap-1 ml-2">
                            <button
                              onClick={() =>
                                feedbackMutation.mutate({ qaId: message.id, thumb: 'up' })
                              }
                              disabled={message.feedback !== null}
                              className={`p-1.5 transition-colors ${
                                message.feedback === 'up'
                                  ? 'text-green-500'
                                  : 'text-gray-400 hover:text-green-500'
                              }`}
                              title="Helpful"
                            >
                              <ThumbsUp size={14} />
                            </button>
                            <button
                              onClick={() =>
                                feedbackMutation.mutate({ qaId: message.id, thumb: 'down' })
                              }
                              disabled={message.feedback !== null}
                              className={`p-1.5 transition-colors ${
                                message.feedback === 'down'
                                  ? 'text-red-500'
                                  : 'text-gray-400 hover:text-red-500'
                              }`}
                              title="Not helpful"
                            >
                              <ThumbsDown size={14} />
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
        <div className="p-4 border-t border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit} className="flex gap-4">
            <textarea
              ref={inputRef}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              className="flex-1 resize-none px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              rows={2}
            />
            <button
              type="submit"
              disabled={!question.trim() || askMutation.isPending}
              className="px-6 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
            >
              {askMutation.isPending ? (
                <Loader2 className="animate-spin" size={20} />
              ) : (
                <Send size={20} />
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Citation panel */}
      {selectedCitation && (
        <div className="w-80 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 flex flex-col">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <h3 className="font-semibold text-gray-900 dark:text-white">Citation</h3>
            <button
              onClick={() => setSelectedCitation(null)}
              className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
            >
              ×
            </button>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <div className="space-y-3">
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Document</p>
                <p className="text-sm text-gray-900 dark:text-white">
                  {selectedCitation.document_name}
                </p>
              </div>
              {selectedCitation.page_number && (
                <div>
                  <p className="text-xs font-medium text-gray-500 mb-1">Page</p>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {selectedCitation.page_number}
                  </p>
                </div>
              )}
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Relevance</p>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full"
                    style={{ width: `${Math.min(selectedCitation.relevance_score * 100, 100)}%` }}
                  />
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-gray-500 mb-1">Excerpt</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                  {selectedCitation.text_snippet}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
