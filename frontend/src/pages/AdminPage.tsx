import { useQuery } from '@tanstack/react-query'
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
} from 'lucide-react'
import { adminApi } from '../api'

export default function AdminPage() {
  // Fetch stats
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['adminStats'],
    queryFn: adminApi.getStats,
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch recent feedback
  const { data: feedbackData, isLoading: feedbackLoading } = useQuery({
    queryKey: ['adminFeedback'],
    queryFn: () => adminApi.getAllFeedback(1, 10),
  })

  // Fetch users
  const { data: usersData, isLoading: usersLoading } = useQuery({
    queryKey: ['adminUsers'],
    queryFn: () => adminApi.getUsers(1, 10),
  })

  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="animate-spin text-primary-600" size={32} />
      </div>
    )
  }

  const statCards = [
    {
      title: 'Total Users',
      value: stats?.total_users || 0,
      icon: Users,
      color: 'blue',
    },
    {
      title: 'Documents',
      value: stats?.total_documents || 0,
      icon: FileText,
      color: 'green',
    },
    {
      title: 'Questions Asked',
      value: stats?.total_questions || 0,
      icon: MessageSquare,
      color: 'purple',
    },
    {
      title: 'Today\'s Questions',
      value: stats?.questions_today || 0,
      icon: TrendingUp,
      color: 'orange',
    },
    {
      title: 'Positive Feedback',
      value: stats?.feedback_positive || 0,
      icon: ThumbsUp,
      color: 'emerald',
    },
    {
      title: 'Negative Feedback',
      value: stats?.feedback_negative || 0,
      icon: ThumbsDown,
      color: 'red',
    },
  ]

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; text: string; icon: string }> = {
      blue: {
        bg: 'bg-blue-50 dark:bg-blue-900/20',
        text: 'text-blue-600 dark:text-blue-400',
        icon: 'bg-blue-100 dark:bg-blue-900/40',
      },
      green: {
        bg: 'bg-green-50 dark:bg-green-900/20',
        text: 'text-green-600 dark:text-green-400',
        icon: 'bg-green-100 dark:bg-green-900/40',
      },
      purple: {
        bg: 'bg-purple-50 dark:bg-purple-900/20',
        text: 'text-purple-600 dark:text-purple-400',
        icon: 'bg-purple-100 dark:bg-purple-900/40',
      },
      orange: {
        bg: 'bg-orange-50 dark:bg-orange-900/20',
        text: 'text-orange-600 dark:text-orange-400',
        icon: 'bg-orange-100 dark:bg-orange-900/40',
      },
      emerald: {
        bg: 'bg-emerald-50 dark:bg-emerald-900/20',
        text: 'text-emerald-600 dark:text-emerald-400',
        icon: 'bg-emerald-100 dark:bg-emerald-900/40',
      },
      red: {
        bg: 'bg-red-50 dark:bg-red-900/20',
        text: 'text-red-600 dark:text-red-400',
        icon: 'bg-red-100 dark:bg-red-900/40',
      },
    }
    return colors[color] || colors.blue
  }

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {statCards.map((stat) => {
          const colors = getColorClasses(stat.color)
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
                  <p className={`text-2xl font-bold ${colors.text}`}>{stat.value.toLocaleString()}</p>
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
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <Clock className="text-yellow-500" size={20} />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.documents_by_status?.pending || 0}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <Loader2 className="text-blue-500" size={20} />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Processing</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.documents_by_status?.processing || 0}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <CheckCircle className="text-green-500" size={20} />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Processed</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.documents_by_status?.processed || 0}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700 rounded-lg">
            <XCircle className="text-red-500" size={20} />
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Failed</p>
              <p className="text-lg font-semibold text-gray-900 dark:text-white">
                {stats?.documents_by_status?.failed || 0}
              </p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Users */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Users</h3>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {usersLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="animate-spin mx-auto text-gray-400" size={24} />
              </div>
            ) : (
              usersData?.users.slice(0, 5).map((user) => (
                <div key={user.id} className="p-4 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-100 dark:bg-primary-900/20 rounded-full flex items-center justify-center">
                      <Users className="text-primary-600 dark:text-primary-400" size={18} />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900 dark:text-white">{user.name}</p>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                  </div>
                  <span
                    className={`px-2 py-1 text-xs rounded-full ${
                      user.role === 'admin'
                        ? 'bg-red-100 text-red-700 dark:bg-red-900/20 dark:text-red-400'
                        : user.role === 'editor'
                        ? 'bg-blue-100 text-blue-700 dark:bg-blue-900/20 dark:text-blue-400'
                        : 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
                    }`}
                  >
                    {user.role}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recent Feedback */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Recent Feedback</h3>
          </div>
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {feedbackLoading ? (
              <div className="p-8 text-center">
                <Loader2 className="animate-spin mx-auto text-gray-400" size={24} />
              </div>
            ) : feedbackData?.feedback.length === 0 ? (
              <div className="p-8 text-center text-gray-500">No feedback yet</div>
            ) : (
              (feedbackData?.feedback as Array<{
                qa_id: string
                question: string
                feedback: string
                created_at: string
              }>)?.slice(0, 5).map((item) => (
                <div key={item.qa_id} className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900 dark:text-white truncate">
                        {item.question}
                      </p>
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
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Feedback Analysis */}
      {stats && stats.total_feedback > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Feedback Analysis</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-500">Satisfaction Rate</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {Math.round(
                    (stats.feedback_positive / stats.total_feedback) * 100
                  )}%
                </span>
              </div>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div
                  className="bg-green-500 h-3 rounded-full transition-all duration-500"
                  style={{
                    width: `${(stats.feedback_positive / stats.total_feedback) * 100}%`,
                  }}
                />
              </div>
            </div>
          </div>
          <div className="mt-4 flex items-center gap-6 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full" />
              <span className="text-gray-600 dark:text-gray-400">
                Positive: {stats.feedback_positive}
              </span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full" />
              <span className="text-gray-600 dark:text-gray-400">
                Negative: {stats.feedback_negative}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
