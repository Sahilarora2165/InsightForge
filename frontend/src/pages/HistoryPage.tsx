import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { format } from 'date-fns';
import { 
  Clock, 
  MessageSquare, 
  ThumbsUp, 
  ThumbsDown,
  Search,
  FileText,
  ChevronRight
} from 'lucide-react';
import { askApi } from '../api';
import type { QAHistoryItem } from '../types';

export function HistoryPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedItem, setSelectedItem] = useState<QAHistoryItem | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ['qa-history'],
    queryFn: () => askApi.getHistory(),
  });

  const history = data?.messages || [];

  const filteredHistory = (history as QAHistoryItem[]).filter((item: QAHistoryItem) => 
    item.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.answer.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex">
      {/* History List */}
      <div className="w-1/2 border-r border-gray-200 dark:border-gray-700 overflow-y-auto">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search history..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
          </div>
        ) : filteredHistory.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <MessageSquare className="h-12 w-12 mb-2" />
            <p>No history found</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredHistory.map((item) => (
              <button
                key={item.session_id}
                onClick={() => setSelectedItem(item)}
                className={`w-full p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors ${
                  selectedItem?.session_id === item.session_id ? 'bg-blue-50 dark:bg-blue-900/20' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                      {item.question}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">
                      {item.answer}
                    </p>
                    <div className="flex items-center gap-2 mt-2">
                      <Clock className="h-3 w-3 text-gray-400" />
                      <span className="text-xs text-gray-400">
                        {format(new Date(item.created_at), 'MMM d, yyyy HH:mm')}
                      </span>
                      {item.feedback && (
                        item.feedback === 'up' ? (
                          <ThumbsUp className="h-3 w-3 text-green-500" />
                        ) : (
                          <ThumbsDown className="h-3 w-3 text-red-500" />
                        )
                      )}
                    </div>
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400 flex-shrink-0" />
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Detail View */}
      <div className="w-1/2 overflow-y-auto">
        {selectedItem ? (
          <div className="p-6">
            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Question
              </h3>
              <p className="text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 p-4 rounded-lg">
                {selectedItem.question}
              </p>
            </div>

            <div className="mb-6">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                Answer
              </h3>
              <div className="text-gray-700 dark:text-gray-300 bg-gray-100 dark:bg-gray-800 p-4 rounded-lg prose dark:prose-invert max-w-none">
                {selectedItem.answer}
              </div>
            </div>

            {selectedItem.citations && selectedItem.citations.length > 0 && (
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  Citations
                </h3>
                <div className="space-y-2">
                  {selectedItem.citations.map((citation, index) => (
                    <div 
                      key={index}
                      className="flex items-start gap-2 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg"
                    >
                      <FileText className="h-4 w-4 text-blue-500 flex-shrink-0 mt-0.5" />
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-white">
                          {citation.document_name}
                        </p>
                        {(citation.page_number || citation.paragraph_number) && (
                          <p className="text-xs text-gray-500">
                            {citation.page_number && `Page ${citation.page_number}`}
                            {citation.page_number && citation.paragraph_number && ', '}
                            {citation.paragraph_number && `Paragraph ${citation.paragraph_number}`}
                          </p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
              <span>Model: {selectedItem.model_name}</span>
              {selectedItem.latency_ms && (
                <span>Latency: {selectedItem.latency_ms}ms</span>
              )}
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full text-gray-500">
            <MessageSquare className="h-12 w-12 mb-2" />
            <p>Select a conversation to view details</p>
          </div>
        )}
      </div>
    </div>
  );
}
