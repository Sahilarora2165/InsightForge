import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users, FileText, MessageSquare, ThumbsUp, ThumbsDown,
  TrendingUp, Clock, CheckCircle, XCircle, Loader2,
  FolderOpen, Zap, Shield, Trash2, UserPlus, BarChart2,
} from 'lucide-react'
import { adminApi } from '../api'
import toast from 'react-hot-toast'

type Tab = 'overview' | 'users' | 'audit'

function useCountUp(target: number, duration = 800) {
  const [count, setCount] = useState(0)
  const raf = useRef<number>(0)
  useEffect(() => {
    if (!target) { setCount(0); return }
    let start: number | null = null
    const animate = (ts: number) => {
      if (!start) start = ts
      const p = Math.min((ts - start) / duration, 1)
      setCount(Math.floor((1 - Math.pow(1 - p, 3)) * target))
      if (p < 1) raf.current = requestAnimationFrame(animate)
    }
    raf.current = requestAnimationFrame(animate)
    return () => cancelAnimationFrame(raf.current)
  }, [target, duration])
  return count
}

function StatCard({ title, value, icon: Icon }: { title: string; value: number | string; icon: any }) {
  const numeric = typeof value === 'number' ? value : 0
  const animated = useCountUp(numeric)
  return (
    <div className="stat-card">
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: '#111', border: '1px solid #1a1a1a' }}>
          <Icon size={16} style={{ color: '#888' }} />
        </div>
        <div>
          <p className="text-xs" style={{ color: '#555' }}>{title}</p>
          <p className="text-xl font-semibold mt-0.5 font-mono" style={{ color: '#fff' }}>
            {typeof value === 'string' ? value : animated.toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  )
}

export default function AdminPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [showCreate, setShowCreate] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', password: '', name: '', role: 'viewer' })

  const { data: stats, isLoading } = useQuery({ queryKey: ['adminStats'], queryFn: adminApi.getStats, refetchInterval: 30000 })
  useQuery({ queryKey: ['adminFeedback'], queryFn: () => adminApi.getAllFeedback(1, 10) })
  const { data: usersData, isLoading: usersLoading } = useQuery({ queryKey: ['adminUsers'], queryFn: () => adminApi.getUsers(1, 50) })
  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ['adminAudit'], queryFn: () => adminApi.getAuditLogs(1, 20), enabled: activeTab === 'audit',
  })
  const { data: perfData } = useQuery({ queryKey: ['adminPerformance'], queryFn: () => adminApi.getPerformanceStats(), refetchInterval: 30000 })

  const createMutation = useMutation({
    mutationFn: () => adminApi.createUser(newUser),
    onSuccess: () => {
      toast.success('User created'); setShowCreate(false)
      setNewUser({ email: '', password: '', name: '', role: 'viewer' })
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
    },
    onError: () => toast.error('Failed to create user'),
  })

  const deleteMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => { toast.success('Deleted'); queryClient.invalidateQueries({ queryKey: ['adminUsers'] }) },
    onError: (err: any) => toast.error(err?.response?.data?.message || 'Cannot delete user'),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => adminApi.updateUser(id, data),
    onSuccess: () => { toast.success('Updated'); queryClient.invalidateQueries({ queryKey: ['adminUsers'] }) },
    onError: () => toast.error('Failed to update'),
  })

  const s = stats as any
  const perf = perfData as any

  if (isLoading) return (
    <div className="flex justify-center items-center h-64">
      <Loader2 className="animate-spin" size={18} style={{ color: '#555' }} />
    </div>
  )

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart2 },
    { id: 'users',    label: 'Users',    icon: Users },
    { id: 'audit',    label: 'Audit',    icon: Shield },
  ]

  return (
    <div className="max-w-5xl mx-auto p-6 space-y-5">
      {/* Tabs */}
      <div className="flex gap-1 p-1 rounded-lg w-fit" style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
        {tabs.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-medium transition-all"
            style={{
              background: activeTab === tab.id ? '#1a1a1a' : 'transparent',
              color: activeTab === tab.id ? '#fff' : '#555',
            }}>
            <tab.icon size={13} />{tab.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW */}
      {activeTab === 'overview' && (
        <div className="space-y-5">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            <StatCard title="Users"       value={s?.total_users || 0}        icon={Users} />
            <StatCard title="Collections" value={s?.total_collections || 0}  icon={FolderOpen} />
            <StatCard title="Documents"   value={s?.total_documents || 0}    icon={FileText} />
            <StatCard title="Questions"   value={s?.total_questions || 0}    icon={MessageSquare} />
            <StatCard title="Today"       value={s?.questions_today || 0}    icon={TrendingUp} />
            <StatCard title="Avg Latency" value={`${s?.avg_latency_ms || 0}ms`} icon={Zap} />
          </div>

          {/* Doc status */}
          <div className="card p-4">
            <p className="text-xs font-medium mb-3" style={{ color: '#555' }}>Document Status</p>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { label: 'Pending',    key: 'pending',    icon: Clock,        color: '#fbbf24' },
                { label: 'Processing', key: 'processing', icon: Loader2,      color: '#60a5fa' },
                { label: 'Processed',  key: 'processed',  icon: CheckCircle,  color: '#4ade80' },
                { label: 'Failed',     key: 'failed',     icon: XCircle,      color: '#f87171' },
              ].map(({ label, key, icon: Icon, color }) => (
                <div key={key} className="flex items-center gap-2 p-3 rounded-lg"
                  style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
                  <Icon size={14} style={{ color }} />
                  <div>
                    <p className="text-xs" style={{ color: '#555' }}>{label}</p>
                    <p className="text-sm font-mono font-semibold" style={{ color }}>{s?.documents_by_status?.[key] || 0}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            {/* Top collections */}
            <div className="card p-4">
              <p className="text-xs font-medium mb-3" style={{ color: '#555' }}>Top Collections</p>
              {s?.top_collections?.length > 0 ? (
                <div className="space-y-3">
                  {s.top_collections.map((col: any, idx: number) => (
                    <div key={idx} className="space-y-1">
                      <div className="flex justify-between text-xs">
                        <span style={{ color: '#888' }}>{col.name}</span>
                        <span className="font-mono" style={{ color: '#555' }}>{col.query_count}</span>
                      </div>
                      <div className="h-0.5 rounded-full" style={{ background: '#1a1a1a' }}>
                        <div className="h-0.5 rounded-full" style={{
                          width: `${(col.query_count / s.top_collections[0].query_count) * 100}%`,
                          background: '#fff',
                        }} />
                      </div>
                    </div>
                  ))}
                </div>
              ) : <p className="text-xs" style={{ color: '#333' }}>No queries yet</p>}
            </div>

            {/* Feedback */}
            <div className="card p-4">
              <p className="text-xs font-medium mb-3" style={{ color: '#555' }}>Satisfaction</p>
              {s?.total_feedback > 0 ? (
                <div className="space-y-3">
                  <div>
                    <div className="flex justify-between mb-1.5">
                      <span className="text-xs" style={{ color: '#555' }}>Rate</span>
                      <span className="text-xs font-mono" style={{ color: '#fff' }}>
                        {Math.round((s.feedback_positive / s.total_feedback) * 100)}%
                      </span>
                    </div>
                    <div className="h-0.5 rounded-full" style={{ background: '#1a1a1a' }}>
                      <div className="h-0.5 rounded-full transition-all" style={{
                        width: `${(s.feedback_positive / s.total_feedback) * 100}%`,
                        background: '#4ade80',
                      }} />
                    </div>
                  </div>
                  <div className="flex gap-3 text-xs">
                    <span className="flex items-center gap-1.5" style={{ color: '#555' }}>
                      <ThumbsUp size={11} style={{ color: '#4ade80' }} />{s.feedback_positive}
                    </span>
                    <span className="flex items-center gap-1.5" style={{ color: '#555' }}>
                      <ThumbsDown size={11} style={{ color: '#f87171' }} />{s.feedback_negative}
                    </span>
                  </div>
                </div>
              ) : <p className="text-xs" style={{ color: '#333' }}>No feedback yet</p>}
            </div>
          </div>

          {/* Perf */}
          {perf && (
            <div className="card p-4">
              <p className="text-xs font-medium mb-3 flex items-center gap-2" style={{ color: '#555' }}>
                <Zap size={12} /> Performance
              </p>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
                {[
                  { label: 'Cache Hit',     value: `${perf?.cache_stats?.hit_rate || 0}%` },
                  { label: 'Cache Size',    value: `${perf?.cache_stats?.cache_size || 0}` },
                  { label: 'API Requests',  value: `${perf?.api_metrics?.total_requests || 0}` },
                  { label: 'Avg Response',  value: `${perf?.api_metrics?.avg_response_time_ms || 0}ms` },
                ].map(({ label, value }) => (
                  <div key={label} className="p-3 rounded-lg" style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}>
                    <p className="text-xs mb-1" style={{ color: '#555' }}>{label}</p>
                    <p className="text-sm font-mono" style={{ color: '#888' }}>{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* USERS */}
      {activeTab === 'users' && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <p className="text-xs" style={{ color: '#555' }}>{usersData?.total || 0} users</p>
            <button onClick={() => setShowCreate(!showCreate)} className="btn btn-primary">
              <UserPlus size={12} /> Add User
            </button>
          </div>

          {showCreate && (
            <div className="card p-4 space-y-3 animate-fade-in">
              <div className="grid grid-cols-2 gap-2">
                <input placeholder="Name" value={newUser.name}
                  onChange={e => setNewUser({ ...newUser, name: e.target.value })}
                  className="input px-3 py-2 text-xs" />
                <input type="email" placeholder="Email" value={newUser.email}
                  onChange={e => setNewUser({ ...newUser, email: e.target.value })}
                  className="input px-3 py-2 text-xs" />
                <input type="password" placeholder="Password" value={newUser.password}
                  onChange={e => setNewUser({ ...newUser, password: e.target.value })}
                  className="input px-3 py-2 text-xs" />
                <select value={newUser.role} onChange={e => setNewUser({ ...newUser, role: e.target.value })}
                  className="input px-3 py-2 text-xs">
                  <option value="viewer">Viewer</option>
                  <option value="editor">Editor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-2">
                <button onClick={() => createMutation.mutate()}
                  disabled={!newUser.email || !newUser.password || !newUser.name || createMutation.isPending}
                  className="btn btn-primary disabled:opacity-40">
                  {createMutation.isPending ? <Loader2 size={12} className="animate-spin" /> : <UserPlus size={12} />}
                  Create
                </button>
                <button onClick={() => setShowCreate(false)} className="btn btn-secondary">Cancel</button>
              </div>
            </div>
          )}

          <div className="card overflow-hidden">
            {usersLoading ? (
              <div className="flex justify-center py-8"><Loader2 className="animate-spin" size={16} style={{ color: '#555' }} /></div>
            ) : (
              usersData?.users.map((user, idx) => (
                <div key={user.id} className="flex items-center gap-3 px-4 py-3"
                  style={{ borderBottom: idx < (usersData.users.length - 1) ? '1px solid #1a1a1a' : 'none' }}>
                  <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                    style={{ background: '#111', border: '1px solid #1a1a1a' }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: '#888' }}>
                      {user.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs font-medium" style={{ color: '#fff' }}>{user.name}</p>
                    <p className="text-xs" style={{ color: '#555' }}>{user.email}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <select value={user.role}
                      onChange={e => updateMutation.mutate({ id: user.id, data: { role: e.target.value } })}
                      className="input px-2 py-1 text-xs" style={{ width: 'auto' }}>
                      <option value="viewer">viewer</option>
                      <option value="editor">editor</option>
                      <option value="admin">admin</option>
                    </select>
                    <span className={`badge ${user.is_active ? 'badge-green' : 'badge-default'}`}>
                      {user.is_active ? 'active' : 'inactive'}
                    </span>
                    <button onClick={() => { if (confirm(`Delete ${user.name}?`)) deleteMutation.mutate(user.id) }}
                      className="btn-danger p-1.5">
                      <Trash2 size={12} />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {/* AUDIT */}
      {activeTab === 'audit' && (
        <div className="card overflow-hidden">
          <div className="px-4 py-3" style={{ borderBottom: '1px solid #1a1a1a' }}>
            <p className="text-xs font-medium" style={{ color: '#888' }}>Audit Log</p>
          </div>
          {auditLoading ? (
            <div className="flex justify-center py-8"><Loader2 className="animate-spin" size={16} style={{ color: '#555' }} /></div>
          ) : (
            (auditData?.logs as any[])?.map((log: any) => (
              <div key={log.id} className="flex items-start gap-3 px-4 py-3"
                style={{ borderBottom: '1px solid #1a1a1a' }}>
                <Shield size={12} className="mt-0.5 flex-shrink-0" style={{ color: '#333' }} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-medium" style={{ color: '#888' }}>
                      {log.action.replace(/_/g, ' ')}
                    </span>
                    {log.resource_type && <span className="badge badge-default">{log.resource_type}</span>}
                  </div>
                  <p className="text-xs font-mono mt-0.5" style={{ color: '#333' }}>
                    {log.ip_address || '—'} · {new Date(log.created_at).toLocaleString()}
                  </p>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  )
}