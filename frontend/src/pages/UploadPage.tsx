import { useState, useCallback, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useDropzone } from 'react-dropzone'
import {
  Upload,
  FileText,
  File,
  Trash2,
  RefreshCw,
  Download,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  FolderOpen,
} from 'lucide-react'
import { documentsApi, collectionsApi } from '../api'
import type { Document } from '../types'
import toast from 'react-hot-toast'

export default function UploadPage() {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const [selectedCollectionId, setSelectedCollectionId] = useState<string>('')

  // Fetch collections for the dropdown
  const { data: collectionsData } = useQuery({
    queryKey: ['collections'],
    queryFn: () => collectionsApi.list(),
  })

  // Fetch documents
  const { data, isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: () => documentsApi.list(1, 50),
  })

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: (file: File) =>
      documentsApi.upload(
        file,
        selectedCollectionId || null,
        (progress) => {
          setUploadProgress((prev) => ({ ...prev, [file.name]: progress }))
        }
      ),
    onSuccess: (_data: any, file: File) => {
      toast.success(`${file.name} uploaded successfully`)
      setUploadProgress((prev) => {
        const { [file.name]: _, ...rest } = prev
        return rest
      })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.refetchQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => {
      toast.error('Failed to upload file')
      setUploadProgress({})
    },
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: documentsApi.delete,
    onSuccess: () => {
      toast.success('Document deleted')
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to delete document'),
  })

  // Reprocess mutation
  const reprocessMutation = useMutation({
    mutationFn: documentsApi.reprocess,
    onSuccess: () => {
      toast.success('Document reprocessing started')
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    },
    onError: () => toast.error('Failed to reprocess document'),
  })

  // Poll for status updates on pending/processing documents
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => {
    const pendingDocs = data?.documents.filter(
      (d) => d.status === 'pending' || d.status === 'processing'
    )

    if (pendingDocs && pendingDocs.length > 0) {
      // Start polling if not already polling
      if (!pollingRef.current) {
        pollingRef.current = setInterval(() => {
          queryClient.invalidateQueries({ queryKey: ['documents'] })
          queryClient.refetchQueries({ queryKey: ['documents'] })
        }, 3000)
      }
    } else {
      // No pending docs — stop polling
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }

    // Cleanup on unmount
    return () => {
      if (pollingRef.current) {
        clearInterval(pollingRef.current)
        pollingRef.current = null
      }
    }
  }, [data?.documents, queryClient])

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      acceptedFiles.forEach((file) => {
        uploadMutation.mutate(file)
      })
    },
    [uploadMutation]
  )

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
    if (!collectionId) return 'Uncategorized'
    const collection = collectionsData?.collections.find((c) => c.id === collectionId)
    return collection?.name || 'Unknown'
  }

  const getStatusIcon = (status: Document['status']) => {
    switch (status) {
      case 'processed':
        return <CheckCircle className="text-green-500" size={18} />
      case 'processing':
        return <Loader2 className="text-blue-500 animate-spin" size={18} />
      case 'pending':
        return <Clock className="text-yellow-500" size={18} />
      case 'failed':
        return <XCircle className="text-red-500" size={18} />
    }
  }

  const getStatusText = (status: Document['status']) => {
    switch (status) {
      case 'processed': return 'Processed'
      case 'processing': return 'Processing...'
      case 'pending': return 'Pending'
      case 'failed': return 'Failed'
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const getFileIcon = (fileType: string) => {
    switch (fileType) {
      case 'pdf': return <FileText className="text-red-500" size={24} />
      case 'docx': return <FileText className="text-blue-500" size={24} />
      case 'md': return <FileText className="text-purple-500" size={24} />
      default: return <File className="text-gray-500" size={24} />
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">

      {/* Collection selector */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
        <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
          <FolderOpen size={16} className="text-primary-600" />
          Upload to Collection
        </label>
        <select
          value={selectedCollectionId}
          onChange={(e) => setSelectedCollectionId(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white text-sm"
        >
          <option value="">My Documents (default)</option>
          {collectionsData?.collections
            .filter((c) => !c.is_default)
            .map((collection) => (
              <option key={collection.id} value={collection.id}>
                {collection.name}
                {collection.description ? ` — ${collection.description}` : ''}
              </option>
            ))}
        </select>
        <p className="text-xs text-gray-500 mt-1">
          Documents will be searchable only within the selected collection.
        </p>
      </div>

      {/* Upload zone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors ${
          isDragActive
            ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-primary-400 hover:bg-gray-50 dark:hover:bg-gray-800'
        }`}
      >
        <input {...getInputProps()} />
        <div className="flex flex-col items-center">
          <div className="w-16 h-16 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center mb-4">
            <Upload className="text-primary-600 dark:text-primary-400" size={32} />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
            {isDragActive ? 'Drop files here' : 'Upload Documents'}
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-2">
            Drag and drop files here, or click to select files
          </p>
          {selectedCollectionId && (
            <p className="text-sm text-primary-600 dark:text-primary-400 font-medium">
              → {getCollectionName(selectedCollectionId)}
            </p>
          )}
          <p className="text-sm text-gray-500 mt-2">
            Supported formats: PDF, DOCX, MD, TXT (max 50MB)
          </p>
        </div>
      </div>

      {/* Upload progress */}
      {Object.entries(uploadProgress).length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-4">
          <h3 className="font-medium text-gray-900 dark:text-white mb-4">Uploading...</h3>
          <div className="space-y-3">
            {Object.entries(uploadProgress).map(([filename, progress]) => (
              <div key={filename}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-700 dark:text-gray-300">{filename}</span>
                  <span className="text-sm text-gray-500">{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Documents list */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="p-4 border-b border-gray-200 dark:border-gray-700">
          <h3 className="font-semibold text-gray-900 dark:text-white">
            All Documents ({data?.total || 0})
          </h3>
        </div>

        {isLoading ? (
          <div className="p-8 text-center">
            <Loader2 className="animate-spin mx-auto text-gray-400" size={32} />
          </div>
        ) : data?.documents.length === 0 ? (
          <div className="p-8 text-center">
            <AlertCircle className="mx-auto text-gray-400 mb-2" size={32} />
            <p className="text-gray-500">No documents uploaded yet</p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {data?.documents.map((doc) => (
              <div
                key={doc.id}
                className="p-4 flex items-center gap-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors"
              >
                <div className="flex-shrink-0">{getFileIcon(doc.file_type)}</div>

                <div className="flex-1 min-w-0">
                  <p className="font-medium text-gray-900 dark:text-white truncate">
                    {doc.original_filename}
                  </p>
                  <div className="flex items-center gap-4 mt-1 text-sm text-gray-500 flex-wrap">
                    <span>{formatFileSize(doc.file_size)}</span>
                    {doc.page_count && <span>{doc.page_count} pages</span>}
                    {doc.chunk_count > 0 && <span>{doc.chunk_count} chunks</span>}
                    <span className="flex items-center gap-1">
                      <FolderOpen size={12} />
                      {getCollectionName(doc.collection_id)}
                    </span>
                    <span>{new Date(doc.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {getStatusIcon(doc.status)}
                  <span
                    className={`text-sm ${
                      doc.status === 'processed' ? 'text-green-600'
                      : doc.status === 'failed' ? 'text-red-600'
                      : doc.status === 'processing' ? 'text-blue-600'
                      : 'text-yellow-600'
                    }`}
                  >
                    {getStatusText(doc.status)}
                  </span>
                </div>

                {doc.error_message && (
                  <div className="text-xs text-red-500 max-w-xs truncate" title={doc.error_message}>
                    {doc.error_message}
                  </div>
                )}

                <div className="flex items-center gap-2">
                  <button
                    onClick={() => window.open(`/api/documents/${doc.id}/download`)}
                    className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                    title="Download"
                  >
                    <Download size={18} />
                  </button>
                  {doc.status === 'failed' && (
                    <button
                      onClick={() => reprocessMutation.mutate(doc.id)}
                      disabled={reprocessMutation.isPending}
                      className="p-2 text-gray-400 hover:text-blue-600 transition-colors disabled:opacity-50"
                      title="Reprocess"
                    >
                      <RefreshCw size={18} />
                    </button>
                  )}
                  <button
                    onClick={() => {
                      if (confirm('Are you sure you want to delete this document?')) {
                        deleteMutation.mutate(doc.id)
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    className="p-2 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                    title="Delete"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}