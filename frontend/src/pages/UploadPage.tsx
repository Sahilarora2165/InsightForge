import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import {
  Upload, FileText, File, Trash2, RefreshCw, Download,
  CheckCircle, XCircle, Clock, Loader2, AlertCircle, FolderOpen,
} from 'lucide-react'
import { documentsApi, collectionsApi } from '../api'
import type { Document } from '../types'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('')
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { data: collectionsData } = useQuery({
    queryKey: ['collections'],
    queryFn: () => collectionsApi.list(),
  })

  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(1, 50),
  })

  // Poll for pending docs
  useEffect(() => {
    const pending = data?.documents.filter(d => d.status === 'pending' || d.status === 'processing')
    if (pending && pending.length > 0) {
      if (!pollingRef.current) {
        pollingRef.current = setInterval(() => {
          queryClient.invalidateQueries({ queryKey: ['documents'] })
          queryClient.refetchQueries({ queryKey: ['documents'] })
        }, 3000)
      }
    } else {
      if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null }
    }
    return () => { if (pollingRef.current) { clearInterval(pollingRef.current); pollingRef.current = null } }
  }, [data?.documents, queryClient])

  const uploadMutation = useMutation({
    mutationFn: (file: File) => documentsApi.upload(file, selectedCollectionId || null,
      (progress) => setUploadProgress(prev => ({ ...prev, [file.name]: progress }))
    ),
    onSuccess: (_data, file) => {
      toast.success(`${file.name} uploaded`)
      setUploadProgress(prev => { const { [file.name]: _, ...rest } = prev; return rest })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.refetchQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => { toast.error('Upload failed'); setUploadProgress({}) },
  })

  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => { toast.success('Deleted'); queryClient.invalidateQueries({ queryKey: ['documents'] }) },
    onError: () => toast.error('Delete failed'),
  })

  const reprocessMutation = useMutation({
    mutationFn: documentsApi.reprocess,
    onSuccess: () => { toast.success('Reprocessing started'); queryClient.invalidateQueries({ queryKey: ['documents'] }) },
    onError: () => toast.error('Reprocess failed'),
  })

  const onDrop = useCallback((files: File[]) => {
    files.forEach(f => uploadMutation.mutate(f))
  }, [uploadMutation])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/markdown': ['.md'],
      'text/plain': ['.txt'],
    },
  })

  const getCollectionName = (collectionId: string | null) => {
    if (!collectionId) return 'Default'
    return collectionsData?.collections.find(c => c.id === collectionId)?.name || '—'
  }

  const statusIcon = (status: Document['status']) => ({
    processed: <CheckCircle size={13} style={{ color: '#4ade80' }} />,
    processing: <Loader2 size={13} className="animate-spin" style={{ color: '#60a5fa' }} />,
    pending:    <Clock size={13} style={{ color: '#fbbf24' }} />,
    failed:     <XCircle size={13} style={{ color: '#f87171' }} />,
  }[status])

  const statusLabel = (status: Document['status']) => ({
    processed: { label: 'Processed', color: '#4ade80' },
    processing: { label: 'Processing', color: '#60a5fa' },
    pending:    { label: 'Pending',   color: '#fbbf24' },
    failed:     { label: 'Failed',    color: '#f87171' },
  }[status])

  const fileIcon = (type: string) => ({
    pdf:  <FileText size={16} style={{ color: '#888' }} />,
    docx: <FileText size={16} style={{ color: '#888' }} />,
    md:   <FileText size={16} style={{ color: '#888' }} />,
  }[type] || <File size={16} style={{ color: '#555' }} />)

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-4">
      {/* Collection selector */}
      <div className="card p-4 flex items-center gap-3">
        <FolderOpen size={15} style={{ color: '#555' }} className="flex-shrink-0" />
        <div className="flex-1">
          <p className="text-xs font-medium mb-1" style={{ color: '#888' }}>Upload to Collection</p>
          <select
            value={selectedCollectionId}
            onChange={(e) => setSelectedCollectionId(e.target.value)}
            className="input px-2.5 py-1.5 text-xs"
            style={{ maxWidth: 280 }}
          >
            <option value="">My Documents (default)</option>
            {collectionsData?.collections.filter(c => !c.is_default).map(c => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Drop zone */}
      <div
        {...getRootProps()}
        className="rounded-xl border-2 border-dashed p-12 text-center cursor-pointer transition-all"
        style={{
          borderColor: isDragActive ? '#fff' : '#1a1a1a',
          background: isDragActive ? '#0a0a0a' : 'transparent',
        }}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 rounded-xl flex items-center justify-center mb-4"
            style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
            <Upload size={20} style={{ color: isDragActive ? '#fff' : '#555' }} />
          </div>
          <p className="text-sm font-medium mb-1" style={{ color: '#fff' }}>
            {isDragActive ? 'Drop to upload' : 'Drop files or click to upload'}
          </p>
          <p className="text-xs" style={{ color: '#555' }}>PDF, DOCX, MD, TXT · max 50MB</p>
        </div>
      </div>

      {/* Progress */}
      {Object.entries(uploadProgress).length > 0 && (
        <div className="card p-4 space-y-3">
          {Object.entries(uploadProgress).map(([filename, progress]) => (
            <div key={filename}>
              <div className="flex justify-between mb-1.5">
                <span className="text-xs" style={{ color: '#888' }}>{filename}</span>
                <span className="text-xs font-mono" style={{ color: '#555' }}>{progress}%</span>
              </div>
              <div className="w-full h-0.5 rounded-full" style={{ background: '#1a1a1a' }}>
                <div className="h-0.5 rounded-full transition-all" style={{ width: `${progress}%`, background: '#fff' }} />
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Documents table */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: '1px solid #1a1a1a' }}>
          <span className="text-xs font-medium" style={{ color: '#888' }}>
            Documents <span className="font-mono" style={{ color: '#555' }}>({data?.total || 0})</span>
          </span>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin" size={18} style={{ color: '#555' }} />
          </div>
        ) : data?.documents.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-2">
            <AlertCircle size={18} style={{ color: '#333' }} />
            <p className="text-xs" style={{ color: '#555' }}>No documents yet</p>
          </div>
        ) : (
          <div>
            {data?.documents.map((doc, idx) => {
              const sl = statusLabel(doc.status)
              return (
                <div key={doc.id}
                  className="flex items-center gap-3 px-4 py-3 transition-colors"
                  style={{ borderBottom: idx < (data.documents.length - 1) ? '1px solid #1a1a1a' : 'none' }}
                  onMouseEnter={e => (e.currentTarget.style.background = '#0a0a0a')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <div className="flex-shrink-0">{fileIcon(doc.file_type)}</div>

                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate" style={{ color: '#fff' }}>
                      {doc.original_filename}
                    </p>
                    <div className="flex items-center gap-3 mt-0.5 text-xs" style={{ color: '#555' }}>
                      <span>{formatSize(doc.file_size)}</span>
                      {doc.page_count && <span>{doc.page_count}p</span>}
                      <span className="flex items-center gap-1">
                        <FolderOpen size={10} />{getCollectionName(doc.collection_id)}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {statusIcon(doc.status)}
                    <span className="text-xs font-mono" style={{ color: sl?.color }}>{sl?.label}</span>
                  </div>

                  <div className="flex items-center gap-0.5 flex-shrink-0">
                    <button onClick={() => window.open(`/api/documents/${doc.id}/download`)}
                      className="btn-ghost p-1.5" title="Download">
                      <Download size={13} />
                    </button>
                    {doc.status === 'failed' && (
                      <button onClick={() => reprocessMutation.mutate(doc.id)}
                        disabled={reprocessMutation.isPending}
                        className="btn-ghost p-1.5 disabled:opacity-40" title="Reprocess">
                        <RefreshCw size={13} />
                      </button>
                    )}
                    <button
                      onClick={() => { if (confirm('Delete this document?')) deleteMutation.mutate(doc.id) }}
                      disabled={deleteMutation.isPending}
                      className="btn-danger p-1.5 disabled:opacity-40" title="Delete">
                      <Trash2 size={13} />
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}