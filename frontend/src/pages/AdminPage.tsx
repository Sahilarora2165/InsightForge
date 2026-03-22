import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Users,
  FileText,
  MessageSquare,
  ThumbsUp,
  ThumbsDown,
  TrendingUp,
  Clock,
  CheckCircle,
  XCircle,
  Loader2,
  FolderOpen,
  Zap,
  Shield,
  Trash2,
  UserPlus,
  BarChart2,
} from 'lucide-react'
import { adminApi } from '../api'
import toast from 'react-hot-toast'

type Tab = 'overview' | 'users' | 'audit'

export default function AdminPage() {
  const queryClient = useQueryClient()
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [showCreateUser, setShowCreateUser] = useState(false)
  const [newUser, setNewUser] = useState({ email: '', password: '', name: '', role: 'viewer' })

  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['adminStats'],
    queryFn: adminApi.getStats,
    refetchInterval: 30000,
  })

  const { data: feedbackData } = useQuery({
    queryKey: ['adminFeedback'],
    queryFn: () => adminApi.getAllFeedback(1, 10),
  })

  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => adminApi.getUsers(1, 50),
  })

  const { data: auditData, isLoading: auditLoading } = useQuery({
    queryKey: ['adminAudit'],
    queryFn: () => adminApi.getAuditLogs(1, 20),
    enabled: activeTab === 'audit',
  })

  const { data: perfData } = useQuery({
    queryKey: ['adminPerformance'],
    queryFn: () => adminApi.getPerformanceStats(),
    refetchInterval: 30000,
  })

  const createUserMutation = useMutation({
    mutationFn: () => adminApi.createUser(newUser),
    onSuccess: () => {
      toast.success('User created successfully')
      setShowCreateUser(false)
      setNewUser({ email: '', password: '', name: '', role: 'viewer' })
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
    },
    onError: () => toast.error('Failed to create user'),
  })

  const deleteUserMutation = useMutation({
    mutationFn: adminApi.deleteUser,
    onSuccess: () => {
      toast.success('User deleted')
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
      queryClient.invalidateQueries({ queryKey: ['adminStats'] })
    },
    onError: () => toast.error('Failed to delete user'),
  })

  const updateUserMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => adminApi.updateUser(id, data),
    onSuccess: () => {
      toast.success('User updated')
      queryClient.invalidateQueries({ queryKey: ['adminUsers'] })
    },
    onError: () => toast.error('Failed to update user'),
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary-600" size={32} />
      </div>
    )
  }

  const statsAsAny = stats as any

  const statCards = [
    { title: 'Total Users', value: statsAsAny?.total_users || 0, icon: Users, color: 'blue' },
    { title: 'Collections', value: statsAsAny?.total_collections || 0, icon: FolderOpen, color: 'indigo' },
    { title: 'Documents', value: statsAsAny?.total_documents || 0, icon: FileText, color: 'green' },
    { title: 'Questions Asked', value: statsAsAny?.total_questions || 0, icon: MessageSquare, color: 'purple' },
    { title: "Today's Questions", value: statsAsAny?.questions_today || 0, icon: TrendingUp, color: 'orange' },
    { title: 'Avg Latency', value: `${statsAsAny?.avg_latency_ms || 0}ms`, icon: Zap, color: 'yellow' },
  ]

  const colorMap: Record<string, { bg: string; text: string; icon: string }> = {
    blue: { bg: 'bg-blue-50 dark:bg-blue-900/20', text: 'text-blue-600 dark:text-blue-400', icon: 'bg-blue-100 dark:bg-blue-900/40' },
    indigo: { bg: 'bg-indigo-50 dark:bg-indigo-900/20', text: 'text-indigo-600 dark:text-indigo-400', icon: 'bg-indigo-100 dark:bg-indigo-900/40' },
    green: { bg: 'bg-green-50 dark:bg-green-900/20', text: 'text-green-600 dark:text-green-400', icon: 'bg-green-100 dark:bg-green-900/40' },
    purple: { bg: 'bg-purple-50 dark:bg-purple-900/20', text: 'text-purple-600 dark:text-purple-400', icon: 'bg-purple-100 dark:bg-purple-900/40' },
    orange: { bg: 'bg-orange-50 dark:bg-orange-900/20', text: 'text-orange-600 dark:text-orange-400', icon: 'bg-orange-100 dark:bg-orange-900/40' },
    yellow: { bg: 'bg-yellow-50 dark:bg-yellow-900/20', text: 'text-yellow-600 dark:text-yellow-400', icon: 'bg-yellow-100 dark:bg-yellow-900/40' },
    emerald: { bg: 'bg-emerald-50 dark:bg-emerald-900/20', text: 'text-emerald-600 dark:text-emerald-400', icon: 'bg-emerald-100 dark:bg-emerald-900/40' },
    red: { bg: 'bg-red-50 dark:bg-red-900/20', text: 'text-red-600 dark:text-red-400', icon: 'bg-red-100 dark:bg-red-900/40' },
  }

  const tabs: { id: Tab; label: string; icon: any }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart2 },
    { id: 'users', label: 'Users', icon: Users },
    { id: 'audit', label: 'Audit Log', icon: Shield },
  ]

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 dark:bg-gray-800 rounded-xl p-1 w-fit">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-white dark:bg-gray-700 text-primary-600 dark:text-primary-400 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200'
            }`}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* OVERVIEW TAB */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {statCards.map((stat) => {
              const colors = colorMap[stat.color]
              return (
                <div
                  key={stat.title}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6"
                >
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 ${colors.icon} rounded-lg flex items-center justify-center`}>
                      <stat.icon className={colors.text} size={24} />
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{stat.title}</p>
                      <p className={`text-2xl font-bold ${colors.text}`}>
                        {typeof stat.value === 'number' ? stat.value.toLocaleString() : stat.value}
                      </p>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Document Status */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Documents by Status</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Pending', key: 'pending', icon: Clock, color: 'text-yellow-500' },
                { label: 'Processing', key: 'processing', icon: Loader2, color: 'text-blue-500' },
                { label: 'Processed', key: 'processed', icon: CheckCircle, color: 'text-green-500' },
                { label: 'Failed', key: 'failed', icon: XCircle, color: 'text-red-500' },
              ].map(({ label, key, icon: Icon, color }) => (
                <div key={key} className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                  <Icon className={color} size={20} />
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{label}</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {statsAsAny?.documents_by_status?.[key] || 0}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Collections */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">Most Queried Collections</h3>
              </div>
              <div className="p-4 space-y-3">
                {statsAsAny?.top_collections?.length > 0 ? (
                  statsAsAny.top_collections.map((col: any, idx: number) => {
                    const maxCount = statsAsAny.top_collections[0].query_count
                    return (
                      <div key={idx} className="space-y-1">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <FolderOpen size={14} className="text-primary-600" />
                            <span className="text-gray-700 dark:text-gray-300">{col.name}</span>
                          </div>
                          <span className="font-medium text-gray-900 dark:text-white">
                            {col.query_count} queries
                          </span>
                        </div>
                        <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                          <div
                            className="bg-primary-500 h-1.5 rounded-full transition-all"
                            style={{ width: `${(col.query_count / maxCount) * 100}%` }}
                          />
                        </div>
                      </div>
                    )
                  })
                ) : (
                  <p className="text-sm text-gray-500 text-center py-4">No collection queries yet</p>
                )}
              </div>
            </div>

            {/* Feedback Analysis */}
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
              <div className="p-4 border-b border-gray-200 dark:border-gray-700">
                <h3 className="font-semibold text-gray-900 dark:text-white">Feedback Analysis</h3>
              </div>
              <div className="p-4">
                {statsAsAny?.total_feedback > 0 ? (
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-sm text-gray-500">Satisfaction Rate</span>
                        <span className="text-sm font-bold text-gray-900 dark:text-white">
                          {Math.round((statsAsAny.feedback_positive / statsAsAny.total_feedback) * 100)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                        <div
                          className="bg-green-500 h-3 rounded-full transition-all duration-500"
                          style={{
                            width: `${(statsAsAny.feedback_positive / statsAsAny.total_feedback) * 100}%`,
                          }}
                        />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div className="flex items-center gap-3 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                        <ThumbsUp className="text-green-500" size={20} />
                        <div>
                          <p className="text-xs text-gray-500">Positive</p>
                          <p className="text-lg font-bold text-green-600">{statsAsAny.feedback_positive}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg">
                        <ThumbsDown className="text-red-500" size={20} />
                        <div>
                          <p className="text-xs text-gray-500">Negative</p>
                          <p className="text-lg font-bold text-red-600">{statsAsAny.feedback_negative}</p>
                        </div>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 text-center py-8">No feedback collected yet</p>
                )}
              </div>
            </div>
          </div>

          {/* Cache + Performance */}
          {perfData && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                <Zap size={18} className="text-yellow-500" />
                System Performance
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {[
                  { label: 'Cache Hit Rate', value: `${(perfData as any)?.cache_stats?.hit_rate || 0}%` },
                  { label: 'Cache Size', value: `${(perfData as any)?.cache_stats?.cache_size || 0} items` },
                  { label: 'Total API Requests', value: (perfData as any)?.api_metrics?.total_requests || 0 },
                  { label: 'Avg API Response', value: `${(perfData as any)?.api_metrics?.avg_response_time_ms || 0}ms` },
                ].map(({ label, value }) => (
                  <div key={label} className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <p className="text-xs text-gray-500 mb-1">{label}</p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">{value}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recent Feedback */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="font-semibold text-gray-900 dark:text-white">Recent Feedback</h3>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {(feedbackData?.feedback as any[])?.length === 0 ? (
                <div className="p-8 text-center text-gray-500 text-sm">No feedback yet</div>
              ) : (
                (feedbackData?.feedback as any[])?.slice(0, 5).map((item: any) => (
                  <div key={item.qa_id} className="p-4 flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-white truncate">{item.question}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {new Date(item.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    {item.feedback === 'up' ? (
                      <ThumbsUp className="text-green-500 flex-shrink-0" size={18} />
                    ) : (
                      <ThumbsDown className="text-red-500 flex-shrink-0" size={18} />
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* USERS TAB */}
      {activeTab === 'users' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-gray-500">{usersData?.total || 0} total users</p>
            <button
              onClick={() => setShowCreateUser(!showCreateUser)}
              className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm transition-colors"
            >
              <UserPlus size={16} />
              Create User
            </button>
          </div>

          {/* Create user form */}
          {showCreateUser && (
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-primary-200 dark:border-primary-800 p-6 space-y-4">
              <h3 className="font-semibold text-gray-900 dark:text-white">Create New User</h3>
              <div className="grid grid-cols-2 gap-4">
                <input
                  type="text"
                  placeholder="Name"
                  value={newUser.name}
                  onChange={(e) => setNewUser({ ...newUser, name: e.target.value })}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
                />
                <input
                  type="email"
                  placeholder="Email"
                  value={newUser.email}
                  onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
                />
                <input
                  type="password"
                  placeholder="Password"
                  value={newUser.password}
                  onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
                />
                <select
                  value={newUser.role}
                  onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                  className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700 dark:text-white text-sm"
                >
                  <option value="viewer">Viewer</option>
                  <option value="editor">Editor</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div className="flex gap-3">
                <button
                  onClick={() => createUserMutation.mutate()}
                  disabled={!newUser.email || !newUser.password || !newUser.name || createUserMutation.isPending}
                  className="flex items-center gap-2 bg-primary-600 hover:bg-primary-700 text-white px-4 py-2 rounded-lg text-sm disabled:opacity-50"
                >
                  {createUserMutation.isPending ? <Loader2 size={14} className="animate-spin" /> : <UserPlus size={14} />}
                  Create
                </button>
                <button
                  onClick={() => setShowCreateUser(false)}
                  className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm text-gray-700 dark:text-gray-300"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Users list */}
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
            {usersLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="animate-spin mx-auto text-gray-400" size={24} />
              </div>
            ) : (
              <div className="divide-y divide-gray-200 dark:divide-gray-700">
                {usersData?.users.map((user) => (
                  <div key={user.id} className="p-4 flex items-center justify-between gap-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center">
                        <Users className="text-primary-600" size={18} />
                      </div>
                      <div>
                        <p className="font-medium text-gray-900 dark:text-white">{user.name}</p>
                        <p className="text-sm text-gray-500">{user.email}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <select
                        value={user.role}
                        onChange={(e) =>
                          updateUserMutation.mutate({ id: user.id, data: { role: e.target.value } })
                        }
                        className="text-xs px-2 py-1 border border-gray-200 dark:border-gray-600 rounded dark:bg-gray-700 dark:text-white"
                      >
                        <option value="viewer">Viewer</option>
                        <option value="editor">Editor</option>
                        <option value="admin">Admin</option>
                      </select>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          user.is_active
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/20 dark:text-green-400'
                            : 'bg-gray-100 text-gray-500'
                        }`}
                      >
                        {user.is_active ? 'Active' : 'Inactive'}
                      </span>
                      <button
                        onClick={() => {
                          if (confirm(`Delete ${user.name}?`)) {
                            deleteUserMutation.mutate(user.id)
                          }
                        }}
                        className="p-1.5 text-gray-400 hover:text-red-600 transition-colors"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* AUDIT LOG TAB */}
      {activeTab === 'audit' && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Audit Log</h3>
            <p className="text-sm text-gray-500 mt-1">All user actions tracked in real time</p>
          </div>
          {auditLoading ? (
            <div className="p-8 text-center">
              <Loader2 className="animate-spin mx-auto text-gray-400" size={24} />
            </div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700">
              {(auditData?.logs as any[])?.length === 0 ? (
                <div className="p-8 text-center text-sm text-gray-500">No audit logs yet</div>
              ) : (
                (auditData?.logs as any[])?.map((log: any) => (
                  <div key={log.id} className="p-4 flex items-start gap-4">
                    <div className="w-8 h-8 bg-gray-100 dark:bg-gray-700 rounded-lg flex items-center justify-center flex-shrink-0">
                      <Shield size={14} className="text-gray-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-sm font-medium text-gray-900 dark:text-white">
                          {log.action.replace(/_/g, ' ')}
                        </span>
                        {log.resource_type && (
                          <span className="text-xs bg-gray-100 dark:bg-gray-700 text-gray-500 px-2 py-0.5 rounded">
                            {log.resource_type}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                        <span>{log.ip_address || 'unknown IP'}</span>
                        <span>{new Date(log.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}