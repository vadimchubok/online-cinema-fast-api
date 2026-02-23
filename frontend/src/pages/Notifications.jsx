import { useState, useEffect } from 'react'
import { getNotifications, markNotificationRead } from '../api/interactions'
import Spinner from '../components/ui/Spinner'

function notifLabel(type) {
  if (type === 'COMMENT_REPLY') return 'replied to your comment'
  if (type === 'COMMENT_LIKE')  return 'liked your comment'
  return type.toLowerCase().replace(/_/g, ' ')
}

export default function Notifications({ setHasUnread }) {
  const [items,   setItems]   = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getNotifications({ limit: 100 })
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : (data.items ?? [])
        setItems(list)
        setHasUnread?.(list.some((n) => !n.is_read))
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [setHasUnread])

  const handleMarkRead = async (id) => {
    try {
      await markNotificationRead(id)
      setItems((prev) => {
        const next = prev.map((n) => n.id === id ? { ...n, is_read: true } : n)
        setHasUnread?.(next.some((n) => !n.is_read))
        return next
      })
    } catch {}
  }

  const markAllRead = async () => {
    const unread = items.filter((n) => !n.is_read)
    await Promise.allSettled(unread.map((n) => markNotificationRead(n.id)))
    setItems((prev) => prev.map((n) => ({ ...n, is_read: true })))
    setHasUnread?.(false)
  }

  const unreadCount = items.filter((n) => !n.is_read).length

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#f1f1f1]">Notifications</h1>
        {unreadCount > 0 && (
          <button
            onClick={markAllRead}
            className="text-sm text-red-500 hover:text-red-400 transition-colors"
          >
            Mark all as read
          </button>
        )}
      </div>

      {loading && <Spinner className="py-16" />}

      {!loading && items.length === 0 && (
        <div className="py-20 text-center space-y-3">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
            className="w-14 h-14 mx-auto text-[#2a2a38]">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0
              00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0
              .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
          <p className="text-[#55556a] text-sm">No notifications yet.</p>
        </div>
      )}

      {!loading && items.length > 0 && (
        <div className="space-y-2">
          {items.map((n) => (
            <div key={n.id}
              className={`flex items-start justify-between gap-3 rounded-xl border px-4 py-3 transition-colors
                ${n.is_read
                  ? 'border-[#1e1e28] bg-[#13131a]'
                  : 'border-[#2a2a38] bg-[#1a1a24]'}`}>
              <div className="flex items-start gap-3 min-w-0">
                <div className={`mt-1.5 w-2 h-2 rounded-full shrink-0
                  ${n.is_read ? 'bg-transparent' : 'bg-red-500'}`} />
                <div className="min-w-0">
                  <p className="text-sm text-[#f1f1f1]">
                    <span className="text-[#9999aa]">
                      User #{n.actor_user_id ?? '?'}
                    </span>
                    {' '}{notifLabel(n.type)}
                  </p>
                  <p className="text-[11px] text-[#55556a] mt-0.5">
                    {new Date(n.created_at).toLocaleDateString('en-US', {
                      month: 'short', day: 'numeric',
                      hour: '2-digit', minute: '2-digit',
                    })}
                  </p>
                </div>
              </div>
              {!n.is_read && (
                <button
                  onClick={() => handleMarkRead(n.id)}
                  className="shrink-0 text-[11px] text-[#55556a] hover:text-[#9999aa]
                    transition-colors whitespace-nowrap"
                >
                  Mark read
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
