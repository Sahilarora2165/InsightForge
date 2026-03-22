import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FolderOpen,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  FileText,
  Users,
  ChevronRight,
  Loader2,
  FolderPlus,
} from 'lucide-react'
import { collectionsApi } from '../api'
import { useUIStore } from '../store/uiStore'
import type { Collection } from '../types'
import toast from 'react-hot-toast'
import { useNavigate } from 'react-router-dom'

export default function CollectionsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { setCurrentCollectionId, setCurrentSessionId } = useUIStore()

  const [showCreateForm, setShowCreateForm] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDescription, setNewDescription] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editDescription, setEditDescription] = useState('')

  // Fetch collections
  const { data, isLoading } = useQuery({
    queryKey: ['collections'],
    queryFn: () => collectionsApi.list(),
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: () =>
      collectionsApi.create({
        name: newName.trim(),
        description: newDescription.trim() || undefined,
      }),
    onSuccess: () => {
      toast.success('Collection created')
      setShowCreateForm(false)
      setNewName('')
      setNewDescription('')
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to create collection'),
  })

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: (id: string) =>
      collectionsApi.update(id, {
        name: editName.trim(),
        description: editDescription.trim() || undefined,
      }),
    onSuccess: () => {
      toast.success('Collection updated')
      setEditingId(null)
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to update collection'),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: collectionsApi.delete,
    onSuccess: () => {
      toast.success('Collection deleted. Documents moved to uncategorized.')
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to delete collection'),
  })

  const startEdit = (collection: Collection) => {
    setEditingId(collection.id)
    setEditName(collection.name)
    setEditDescription(collection.description || '')
  }

  const openCollectionChat = (collectionId: string) => {
    setCurrentCollectionId(collectionId)
    setCurrentSessionId(null)
    navigate('/')
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Collections</h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Organize your documents into collections. Chat is scoped to one collection at a time.
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={18} />
          New Collection
        </button>
      </div>

      {/* Create form */}
      {showCreateForm && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-primary-200 dark:border-primary-800 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <FolderPlus size={18} className="text-primary-600" />
            Create New Collection
          </h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Name <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="e.g. HR Policies, Engineering Docs"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
                autoFocus
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Description
              </label>
              <input
                type="text"
                value={newDescription}
                onChange={(e) => setNewDescription(e.target.value)}
                placeholder="Optional description"
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent dark:bg-gray-700 dark:text-white"
              />
            </div>
            <div className="flex gap-3">
              <button
                onClick={() => createMutation.mutate()}
                disabled={!newName.trim() || createMutation.isPending}
                className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors disabled:opacity-50"
              >
                {createMutation.isPending ? (
                  <Loader2 size={16} className="animate-spin" />
                ) : (
                  <Check size={16} />
                )}
                Create
              </button>
              <button
                onClick={() => {
                  setShowCreateForm(false)
                  setNewName('')
                  setNewDescription('')
                }}
                className="flex items-center gap-2 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <X size={16} />
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Collections list */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <Loader2 className="animate-spin text-primary-600" size={32} />
        </div>
      ) : !data?.collections.length ? (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-16 text-center">
          <FolderOpen className="mx-auto text-gray-300 dark:text-gray-600 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            No collections yet
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            Create a collection to organize your documents and scope your chats.
          </p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="inline-flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={18} />
            Create your first collection
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.collections.map((collection) => (
            <div
              key={collection.id}
              className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6 hover:border-primary-300 dark:hover:border-primary-700 transition-colors"
            >
              {editingId === collection.id ? (
                // Edit mode
                <div className="space-y-3">
                  <input
                    type="text"
                    value={editName}
                    onChange={(e) => setEditName(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                    autoFocus
                  />
                  <input
                    type="text"
                    value={editDescription}
                    onChange={(e) => setEditDescription(e.target.value)}
                    placeholder="Description (optional)"
                    className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-white"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => updateMutation.mutate(collection.id)}
                      disabled={!editName.trim() || updateMutation.isPending}
                      className="flex items-center gap-1 bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-sm transition-colors disabled:opacity-50"
                    >
                      {updateMutation.isPending ? (
                        <Loader2 size={14} className="animate-spin" />
                      ) : (
                        <Check size={14} />
                      )}
                      Save
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="flex items-center gap-1 px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <X size={14} />
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                // View mode
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1 min-w-0">
                    <div className="w-12 h-12 bg-primary-100 dark:bg-primary-900/30 rounded-xl flex items-center justify-center flex-shrink-0">
                      <FolderOpen className="text-primary-600 dark:text-primary-400" size={24} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900 dark:text-white">
                          {collection.name}
                        </h3>
                        {collection.is_default && (
                          <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-0.5 rounded-full">
                            Default
                          </span>
                        )}
                      </div>
                      {collection.description && (
                        <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                          {collection.description}
                        </p>
                      )}
                      <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <FileText size={14} />
                          {collection.document_count} documents
                        </span>
                        <span className="flex items-center gap-1">
                          <Users size={14} />
                          {collection.member_count} members
                        </span>
                        <span>
                          {new Date(collection.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={() => openCollectionChat(collection.id)}
                      className="flex items-center gap-1.5 bg-primary-600 hover:bg-primary-700 text-white px-3 py-1.5 rounded-lg text-sm transition-colors"
                      title="Chat with this collection"
                    >
                      Chat
                      <ChevronRight size={14} />
                    </button>
                    <button
                      onClick={() => startEdit(collection)}
                      className="p-2 text-gray-400 hover:text-primary-600 dark:hover:text-primary-400 transition-colors"
                      title="Edit collection"
                    >
                      <Edit2 size={16} />
                    </button>
                    {!collection.is_default && (
                      <button
                        onClick={() => {
                          if (
                            confirm(
                              `Delete "${collection.name}"? Documents will be moved to uncategorized.`
                            )
                          ) {
                            deleteMutation.mutate(collection.id)
                          }
                        }}
                        disabled={deleteMutation.isPending}
                        className="p-2 text-gray-400 hover:text-red-600 transition-colors disabled:opacity-50"
                        title="Delete collection"
                      >
                        <Trash2 size={16} />
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}