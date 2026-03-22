import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { format } from 'date-fns'
import { Clock, MessageSquare, ThumbsUp, ThumbsDown, Search, FileText, Loader2 } from 'lucide-react'
import { askApi } from '../api'
import type { QAHistoryItem } from '../types'

export function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedItem, setSelectedItem] = useState<QAHistoryItem | null>(null)

  const { data, isLoading } = useQuery({
    queryKey: ['qa-history'],
    queryFn: () => askApi.getHistory(),
  })

  const history = data?.messages || []
  const filtered = (history as QAHistoryItem[]).filter(item =>
    item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.answer.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex h-full overflow-hidden">
      {/* List */}
      <div className="w-80 flex-shrink-0 flex flex-col overflow-hidden"
        style={{ borderRight: '1px solid #1a1a1a' }}>
        {/* Search */}
        <div className="p-3 flex-shrink-0" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <div className="relative">
            <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2" style={{ color: '#555' }} />
            <input
              type="text"
              placeholder="Search history…"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="input pl-8 pr-3 py-2 text-xs"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="animate-spin" size={18} style={{ color: '#555' }} />
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 gap-2">
              <MessageSquare size={18} style={{ color: '#333' }} />
              <p className="text-xs" style={{ color: '#555' }}>No history found</p>
            </div>
          ) : (
            filtered.map((item) => (
              <button
                key={item.id}
                onClick={() => setSelectedItem(item)}
                className="w-full text-left px-4 py-3 transition-colors"
                style={{
                  background: selectedItem?.id === item.id ? '#0a0a0a' : 'transparent',
                  borderBottom: '1px solid #1a1a1a',
                }}
                onMouseEnter={e => { if (selectedItem?.id !== item.id) e.currentTarget.style.background = '#050505' }}
                onMouseLeave={e => { if (selectedItem?.id !== item.id) e.currentTarget.style.background = 'transparent' }}
              >
                <p className="text-xs font-medium truncate" style={{ color: '#fff' }}>
                  {item.question}
                </p>
                <p className="text-xs mt-1 line-clamp-2" style={{ color: '#555' }}>
                  {item.answer}
                </p>
                <div className="flex items-center gap-2 mt-2">
                  <Clock size={10} style={{ color: '#333' }} />
                  <span className="text-xs font-mono" style={{ color: '#333' }}>
                    {format(new Date(item.created_at), 'MMM d, HH:mm')}
                  </span>
                  {item.feedback === 'up' && <ThumbsUp size={10} style={{ color: '#4ade80' }} />}
                  {item.feedback === 'down' && <ThumbsDown size={10} style={{ color: '#f87171' }} />}
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 overflow-y-auto">
        {selectedItem ? (
          <div className="p-6 max-w-2xl space-y-5">
            <div>
              <p className="text-xs font-medium mb-2" style={{ color: '#555' }}>Question</p>
              <div className="p-4 rounded-xl text-sm" style={{
                background: '#0a0a0a', border: '1px solid #1a1a1a', color: '#fff', lineHeight: 1.6,
              }}>
                {selectedItem.question}
              </div>
            </div>

            <div>
              <p className="text-xs font-medium mb-2" style={{ color: '#555' }}>Answer</p>
              <div className="p-4 rounded-xl text-sm" style={{
                background: '#0a0a0a', border: '1px solid #1a1a1a', color: '#888', lineHeight: 1.7,
              }}>
                {selectedItem.answer}
              </div>
            </div>

            {selectedItem.citations?.length > 0 && (
              <div>
                <p className="text-xs font-medium mb-2" style={{ color: '#555' }}>Sources</p>
                <div className="space-y-1.5">
                  {selectedItem.citations.map((citation, idx) => (
                    <div key={idx} className="flex items-center gap-2 p-2.5 rounded-lg"
                      style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
                      <FileText size={12} style={{ color: '#555' }} />
                      <div>
                        <p className="text-xs font-medium" style={{ color: '#fff' }}>{citation.document_name}</p>
                        {(citation.page_number || citation.paragraph_number) && (
                          <p className="text-xs font-mono mt-0.5" style={{ color: '#555' }}>
                            {citation.page_number && `p.${citation.page_number}`}
                            {citation.page_number && citation.paragraph_number && ' · '}
                            {citation.paragraph_number && `¶${citation.paragraph_number}`}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 text-xs font-mono pt-2" style={{ color: '#333', borderTop: '1px solid #1a1a1a' }}>
              <span>{selectedItem.model_name}</span>
              {selectedItem.latency_ms && <span>{selectedItem.latency_ms}ms</span>}
              <span>{format(new Date(selectedItem.created_at), 'MMM d, yyyy HH:mm')}</span>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full gap-2">
            <MessageSquare size={20} style={{ color: '#333' }} />
            <p className="text-xs" style={{ color: '#555' }}>Select a conversation</p>
          </div>
        )}
      </div>
    </div>
  )
}