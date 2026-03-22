import { useState } from 'react'
import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import {
  MessageSquare, Upload, Settings, LogOut,
  History, FolderOpen, Zap, ChevronDown,
  PanelLeftClose, PanelLeft,
} from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useUIStore } from '../store/uiStore'
import { authApi } from '../api'
import toast from 'react-hot-toast'

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  const { user, logout: authLogout } = useAuthStore()
  const { sidebarOpen, toggleSidebar } = useUIStore()
  const [userMenuOpen, setUserMenuOpen] = useState(false)

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    authLogout()
    navigate('/login')
    toast.success('Signed out')
  }

  const navigation = [
    { name: 'Chat',        href: '/',            icon: MessageSquare },
    { name: 'Collections', href: '/collections', icon: FolderOpen },
    { name: 'History',     href: '/history',     icon: History },
    { name: 'Upload',      href: '/upload',      icon: Upload },
    { name: 'Admin',       href: '/admin',       icon: Settings, roles: ['admin'] },
  ]

  const filteredNav = navigation.filter(
    (item) => !item.roles || (user && item.roles.includes(user.role))
  )

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: '#000' }}>
      {/* ── Sidebar ── */}
      <aside
        className="flex flex-col flex-shrink-0 transition-all duration-200"
        style={{
          width: sidebarOpen ? '220px' : '52px',
          background: '#000',
          borderRight: '1px solid #1a1a1a',
        }}
      >
        {/* Logo row */}
        <div className="flex items-center h-14 px-3 flex-shrink-0"
          style={{ borderBottom: '1px solid #1a1a1a' }}>
          {sidebarOpen ? (
            <div className="flex items-center justify-between w-full">
              <div className="flex items-center gap-2">
                <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                  style={{ background: '#ffffff' }}>
                  <Zap size={13} style={{ color: '#000000' }} />
                </div>
                <span className="logo-text">InsightForge</span>
              </div>
              <button onClick={toggleSidebar} className="btn-ghost p-1.5">
                <PanelLeftClose size={15} />
              </button>
            </div>
          ) : (
            <button onClick={toggleSidebar} className="btn-ghost p-1.5 w-full flex justify-center">
              <PanelLeft size={15} />
            </button>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto py-3 px-2 space-y-0.5">
          {filteredNav.map((item) => {
            const isActive = location.pathname === item.href
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`nav-item ${isActive ? 'active' : ''}`}
                title={!sidebarOpen ? item.name : undefined}
              >
                <item.icon size={16} className="flex-shrink-0" />
                {sidebarOpen && <span>{item.name}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User row */}
        <div className="flex-shrink-0 p-2" style={{ borderTop: '1px solid #1a1a1a' }}>
          {sidebarOpen ? (
            <div className="flex items-center gap-2.5 px-2 py-2 rounded-lg"
              style={{ background: '#0a0a0a' }}>
              <div className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
                style={{ background: '#1a1a1a', border: '1px solid #222' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#888' }}>
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium truncate" style={{ color: '#fff' }}>{user?.name}</p>
                <p className="text-xs truncate" style={{ color: '#555', fontSize: 11 }}>{user?.role}</p>
              </div>
              <button onClick={handleLogout} className="btn-ghost p-1" title="Sign out">
                <LogOut size={13} style={{ color: '#555' }} />
              </button>
            </div>
          ) : (
            <button onClick={handleLogout} className="btn-ghost w-full flex justify-center p-2" title="Sign out">
              <LogOut size={15} />
            </button>
          )}
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="flex items-center justify-between h-14 px-5 flex-shrink-0"
          style={{ borderBottom: '1px solid #1a1a1a', background: '#000' }}>
          <span className="text-sm font-medium" style={{ color: '#fff' }}>
            {filteredNav.find(i => i.href === location.pathname)?.name || 'InsightForge'}
          </span>

          <div className="relative">
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="flex items-center gap-2 px-3 py-1.5 rounded-lg transition-colors"
              style={{ background: '#0a0a0a', border: '1px solid #1a1a1a' }}
            >
              <div className="w-6 h-6 rounded-full flex items-center justify-center"
                style={{ background: '#1a1a1a' }}>
                <span style={{ fontSize: 11, fontWeight: 600, color: '#888' }}>
                  {user?.name?.charAt(0).toUpperCase()}
                </span>
              </div>
              <span className="text-xs font-medium" style={{ color: '#888' }}>{user?.name}</span>
              <ChevronDown size={12} style={{ color: '#555' }} />
            </button>

            {userMenuOpen && (
              <div className="absolute right-0 mt-1.5 w-48 rounded-xl py-1 z-50 animate-fade-in"
                style={{ background: '#0a0a0a', border: '1px solid #1a1a1a', boxShadow: '0 20px 40px rgba(0,0,0,0.8)' }}>
                <div className="px-3 py-2.5" style={{ borderBottom: '1px solid #1a1a1a' }}>
                  <p className="text-xs font-medium" style={{ color: '#fff' }}>{user?.name}</p>
                  <p className="text-xs mt-0.5" style={{ color: '#555' }}>{user?.email}</p>
                </div>
                <button onClick={handleLogout}
                  className="flex items-center gap-2 w-full px-3 py-2 text-xs transition-colors"
                  style={{ color: '#ef4444' }}
                  onMouseEnter={e => (e.currentTarget.style.background = 'rgba(239,68,68,0.08)')}
                  onMouseLeave={e => (e.currentTarget.style.background = 'transparent')}
                >
                  <LogOut size={13} /> Sign out
                </button>
              </div>
            )}
          </div>
        </header>

        {/* Page */}
        <main className="flex-1 overflow-auto" style={{ background: '#000' }}>
          <Outlet />
        </main>
      </div>

      {userMenuOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setUserMenuOpen(false)} />
      )}
    </div>
  )
}