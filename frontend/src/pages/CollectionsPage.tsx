import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  FolderOpen, Plus, Trash2, Edit2, Check, X,
  FileText, Users, Loader2, MessageSquare,
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

  const [showCreate, setShowCreate] = useState(false)
  const [newName, setNewName] = useState('')
  const [newDesc, setNewDesc] = useState('')
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editName, setEditName] = useState('')
  const [editDesc, setEditDesc] = useState('')

  const { data, isLoading } = useQuery({ queryKey: ['collections'], queryFn: () => collectionsApi.list() })

  const createMutation = useMutation({
    mutationFn: () => collectionsApi.create({ name: newName.trim(), description: newDesc.trim() || undefined }),
    onSuccess: () => {
      toast.success('Collection created')
      setShowCreate(false); setNewName(''); setNewDesc('')
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to create'),
  })

  const updateMutation = useMutation({
    mutationFn: (id: string) => collectionsApi.update(id, { name: editName.trim(), description: editDesc.trim() || undefined }),
    onSuccess: () => {
      toast.success('Updated')
      setEditingId(null)
      queryClient.invalidateQueries({ queryKey: ['collections'] })
    },
    onError: () => toast.error('Failed to update'),
  })

  const deleteMutation = useMutation({
    mutationFn: collectionsApi.delete,
    onSuccess: () => { toast.success('Deleted'); queryClient.invalidateQueries({ queryKey: ['collections'] }) },
    onError: () => toast.error('Failed to delete'),
  })

  const startEdit = (c: Collection) => {
    setEditingId(c.id); setEditName(c.name); setEditDesc(c.description || '')
  }

  const openChat = (id: string) => {
    setCurrentCollectionId(id); setCurrentSessionId(null); navigate('/')
  }

  return (
    <div className="max-w-3xl mx-auto p-6 space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-base font-semibold" style={{ color: '#fff' }}>Collections</h2>
          <p className="text-xs mt-0.5" style={{ color: '#555' }}>
            Organize documents. Chat is scoped per collection.
          </p>
        </div>
        <button onClick={() => setShowCreate(true)} className="btn btn-primary">
          <Plus size={13} /> New
        </button>
      </div>

      {/* Create form */}
      {showCreate && (
        <div className="card p-4 space-y-3 animate-fade-in">
          <p className="text-xs font-medium" style={{ color: '#888' }}>New Collection</p>
          <input type="text" value={newName} onChange={e => setNewName(e.target.value)}
            placeholder="Name" autoFocus className="input px-3 py-2 text-sm" />
          <input type="text" value={newDesc} onChange={e => setNewDesc(e.target.value)}
            placeholder="Description (optional)" className="input px-3 py-2 text-sm" />
          <div className="flex gap-2">
            <button onClick={() => createMutation.mutate()} disabled={!newName.trim() || createMutation.isPending}
              className="btn btn-primary disabled:opacity-40">
              {createMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <Check size={12} />}
              Create
            </button>
            <button onClick={() => { setShowCreate(false); setNewName(''); setNewDesc('') }}
              className="btn btn-secondary">
              <X size={12} /> Cancel
            </button>
          </div>
        </div>
      )}

      {/* List */}
      {isLoading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="animate-spin" size={18} style={{ color: '#555' }} />
        </div>
      ) : !data?.collections.length ? (
        <div className="card p-12 text-center">
          <FolderOpen size={28} className="mx-auto mb-3" style={{ color: '#333' }} />
          <p className="text-sm font-medium mb-1" style={{ color: '#fff' }}>No collections</p>
          <p className="text-xs mb-4" style={{ color: '#555' }}>Create one to organize your documents.</p>
          <button onClick={() => setShowCreate(true)} className="btn btn-primary">
            <Plus size={12} /> Create
          </button>
        </div>
      ) : (
        <div className="card overflow-hidden">
          {data.collections.map((collection, idx) => (
            <div
              key={collection.id}
              className="px-4 py-3.5 transition-colors"
              style={{ borderBottom: idx < data.collections.length - 1 ? '1px solid #1a1a1a' : 'none' }}
              onMouseEnter={e => (e.currentTarget.style.background = '#0a0a0a')}
              onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
            >
              {editingId === collection.id ? (
                <div className="space-y-2">
                  <input type="text" value={editName} onChange={e => setEditName(e.target.value)}
                    className="input px-3 py-2 text-sm" autoFocus />
                  <input type="text" value={editDesc} onChange={e => setEditDesc(e.target.value)}
                    placeholder="Description (optional)" className="input px-3 py-2 text-sm" />
                  <div className="flex gap-2">
                    <button onClick={() => updateMutation.mutate(collection.id)}
                      disabled={!editName.trim() || updateMutation.isPending}
                      className="btn btn-primary disabled:opacity-40 py-1 px-3 text-xs">
                      {updateMutation.isPending ? <Loader2 size={11} className="animate-spin" /> : <Check size={11} />}
                      Save
                    </button>
                    <button onClick={() => setEditingId(null)} className="btn btn-secondary py-1 px-3 text-xs">
                      <X size={11} /> Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0"
                    style={{ background: '#111', border: '1px solid #1a1a1a' }}>
                    <FolderOpen size={15} style={{ color: '#555' }} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium" style={{ color: '#fff' }}>{collection.name}</span>
                      {collection.is_default && (
                        <span className="badge badge-default">default</span>
                      )}
                    </div>
                    {collection.description && (
                      <p className="text-xs mt-0.5 truncate" style={{ color: '#555' }}>{collection.description}</p>
                    )}
                    <div className="flex items-center gap-3 mt-1 text-xs" style={{ color: '#333' }}>
                      <span className="flex items-center gap-1"><FileText size={10} />{collection.document_count}</span>
                      <span className="flex items-center gap-1"><Users size={10} />{collection.member_count}</span>
                      <span>{new Date(collection.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button onClick={() => openChat(collection.id)}
                      className="btn btn-secondary py-1 px-2.5 text-xs gap-1">
                      <MessageSquare size={11} /> Chat
                    </button>
                    <button onClick={() => startEdit(collection)} className="btn-ghost p-1.5" title="Edit">
                      <Edit2 size={13} />
                    </button>
                    {!collection.is_default && (
                      <button
                        onClick={() => { if (confirm(`Delete "${collection.name}"?`)) deleteMutation.mutate(collection.id) }}
                        disabled={deleteMutation.isPending}
                        className="btn-danger p-1.5 disabled:opacity-40" title="Delete">
                        <Trash2 size={13} />
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