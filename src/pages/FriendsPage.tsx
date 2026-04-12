import { useState, useEffect, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { slideUp } from '../lib/motion'
import {
  X,
  UserPlus,
  UserCheck,
  UserX,
  Loader2,
  Mail,
  ChevronLeft,
  Star,
} from 'lucide-react'
import { api } from '../lib/api'

interface FriendItem {
  id: number
  user_id: number
  full_name: string
  email: string | null
  is_favorite: boolean
}

interface SearchUser {
  id: number
  full_name: string
  email: string | null
}

interface Props {
  onClose: () => void
}

export default function FriendsPage({ onClose }: Props) {
  const [friends, setFriends] = useState<FriendItem[]>([])
  const [pendingIn, setPendingIn] = useState<FriendItem[]>([])
  const [pendingOut, setPendingOut] = useState<FriendItem[]>([])
  const [loading, setLoading] = useState(true)

  // Search
  const [showSearch, setShowSearch] = useState(false)
  const [query, setQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchUser[]>([])
  const [searchLoading, setSearchLoading] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined)

  const fetchFriends = useCallback(async () => {
    try {
      const res = await api<{
        success: boolean
        friends: FriendItem[]
        pending_incoming: FriendItem[]
        pending_outgoing: FriendItem[]
      }>('/api/friends')
      if (res.success) {
        setFriends(res.friends)
        setPendingIn(res.pending_incoming)
        setPendingOut(res.pending_outgoing)
      }
    } catch { /* ignore */ }
    finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchFriends()
  }, [fetchFriends])

  useEffect(() => {
    clearTimeout(debounceRef.current)
    if (query.length < 3) {
      setSearchResults([])
      return
    }
    debounceRef.current = setTimeout(async () => {
      setSearchLoading(true)
      try {
        const res = await api<{ success: boolean; users: SearchUser[] }>(
          `/api/friends/search?q=${encodeURIComponent(query)}`,
        )
        setSearchResults(res.users || [])
      } catch { /* ignore */ }
      finally {
        setSearchLoading(false)
      }
    }, 300)
    return () => clearTimeout(debounceRef.current)
  }, [query])

  const sendRequest = async (userId: number) => {
    try {
      const res = await api<{ success: boolean; message: string }>('/api/friends/request', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      })
      if (res.success) {
        setSearchResults((prev) => prev.filter((u) => u.id !== userId))
        fetchFriends()
      }
    } catch { /* ignore */ }
  }

  const respond = async (id: number, action: 'accept' | 'reject') => {
    try {
      await api('/api/friends/respond', {
        method: 'POST',
        body: JSON.stringify({ id, action }),
      })
      fetchFriends()
    } catch { /* ignore */ }
  }

  const removeFriend = async (userId: number) => {
    try {
      await api('/api/friends/remove', {
        method: 'POST',
        body: JSON.stringify({ user_id: userId }),
      })
      setFriends((prev) => prev.filter((f) => f.user_id !== userId))
    } catch { /* ignore */ }
  }

  if (loading) {
    return (
      <div className="flex-1 flex justify-center items-center">
        <Loader2 size={24} className="animate-spin text-brand" />
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6">
      <motion.div variants={slideUp} initial="enter" animate="active" className="space-y-5">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button onClick={onClose} className="text-text-muted hover:text-text-primary transition-colors">
              <ChevronLeft size={24} />
            </button>
            <h1 className="text-2xl font-semibold text-text-primary">Друзья</h1>
          </div>
          <button
            onClick={() => setShowSearch(!showSearch)}
            className="p-2 text-text-muted hover:text-brand transition-colors"
          >
            {showSearch ? <X size={20} /> : <UserPlus size={20} />}
          </button>
        </div>

        {/* Search */}
        <AnimatePresence>
          {showSearch && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              className="overflow-hidden space-y-3"
            >
              <div className="relative">
                <Mail size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-muted" />
                <input
                  type="text"
                  placeholder="Поиск по email или имени..."
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  className="w-full pl-9 pr-4 py-3 bg-surface-2 border border-border rounded-xl text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:border-border-active transition-colors"
                  autoFocus
                />
              </div>

              {searchLoading && (
                <div className="flex justify-center py-3">
                  <Loader2 size={16} className="animate-spin text-text-muted" />
                </div>
              )}

              {searchResults.map((u) => (
                <motion.div
                  key={u.id}
                  initial={{ opacity: 0, y: 4 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="flex items-center justify-between bg-surface-2 rounded-xl border border-border p-3"
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium text-text-primary truncate">{u.full_name}</p>
                    {u.email && <p className="text-xs text-text-muted truncate">{u.email}</p>}
                  </div>
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => sendRequest(u.id)}
                    className="p-2 text-brand hover:bg-brand-glow rounded-lg transition-colors"
                  >
                    <UserPlus size={18} />
                  </motion.button>
                </motion.div>
              ))}

              {query.length >= 3 && !searchLoading && searchResults.length === 0 && (
                <p className="text-xs text-text-muted text-center py-2">Никого не найдено</p>
              )}
            </motion.div>
          )}
        </AnimatePresence>

        {/* Pending incoming */}
        {pendingIn.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-sm font-medium text-text-secondary px-1">
              Входящие запросы ({pendingIn.length})
            </h2>
            {pendingIn.map((f) => (
              <motion.div
                key={f.id}
                layout
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex items-center justify-between bg-surface-2 rounded-xl border border-brand/20 p-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text-primary truncate">{f.full_name}</p>
                  {f.email && <p className="text-xs text-text-muted truncate">{f.email}</p>}
                </div>
                <div className="flex gap-1">
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => respond(f.id, 'accept')}
                    className="p-2 text-success hover:bg-success/10 rounded-lg transition-colors"
                  >
                    <UserCheck size={18} />
                  </motion.button>
                  <motion.button
                    whileTap={{ scale: 0.9 }}
                    onClick={() => respond(f.id, 'reject')}
                    className="p-2 text-danger hover:bg-danger/10 rounded-lg transition-colors"
                  >
                    <UserX size={18} />
                  </motion.button>
                </div>
              </motion.div>
            ))}
          </div>
        )}

        {/* Pending outgoing */}
        {pendingOut.length > 0 && (
          <div className="space-y-2">
            <h2 className="text-sm font-medium text-text-secondary px-1">
              Отправленные ({pendingOut.length})
            </h2>
            {pendingOut.map((f) => (
              <div
                key={f.id}
                className="flex items-center justify-between bg-surface-2 rounded-xl border border-border p-3"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-text-primary truncate">{f.full_name}</p>
                  {f.email && <p className="text-xs text-text-muted truncate">{f.email}</p>}
                </div>
                <span className="text-xs text-text-muted">Ожидает</span>
              </div>
            ))}
          </div>
        )}

        {/* Friends list */}
        <div className="space-y-2">
          <h2 className="text-sm font-medium text-text-secondary px-1">
            Друзья ({friends.length})
          </h2>
          {friends.length > 0 ? (
            friends.map((f) => (
              <motion.div
                key={f.id}
                layout
                className="flex items-center justify-between bg-surface-2 rounded-xl border border-border p-3"
              >
                <div className="flex items-center gap-3 min-w-0 flex-1">
                  <div className="w-9 h-9 bg-surface-3 rounded-full flex items-center justify-center shrink-0">
                    <span className="text-xs font-medium text-text-secondary">
                      {f.full_name.charAt(0)}
                    </span>
                  </div>
                  <div className="min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">{f.full_name}</p>
                    {f.email && <p className="text-xs text-text-muted truncate">{f.email}</p>}
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  {f.is_favorite && <Star size={14} className="text-warning fill-warning" />}
                  <button
                    onClick={() => removeFriend(f.user_id)}
                    className="p-1.5 text-text-muted hover:text-danger transition-colors"
                  >
                    <X size={14} />
                  </button>
                </div>
              </motion.div>
            ))
          ) : (
            <div className="text-center py-8">
              <UserPlus size={40} className="mx-auto text-text-muted mb-3" />
              <p className="text-sm text-text-secondary">Нет друзей</p>
              <p className="text-xs text-text-muted mt-1">
                Нажмите + чтобы найти по email
              </p>
            </div>
          )}
        </div>
      </motion.div>
    </div>
  )
}
