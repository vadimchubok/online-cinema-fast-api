import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { getMyOrders, cancelOrder } from '../api/orders'

// ─── status badge ──────────────────────────────────────────────────────────────

const STATUS_STYLE = {
  PENDING:   'bg-yellow-950/50 text-yellow-400 border-yellow-700/40',
  PAID:      'bg-green-950/50  text-green-400  border-green-700/40',
  CANCELLED: 'bg-[#1a1a24]    text-[#55556a]  border-[#2a2a38]',
}

function StatusBadge({ status }) {
  return (
    <span className={`text-[11px] font-semibold px-2 py-0.5 rounded border
      uppercase tracking-wide ${STATUS_STYLE[status] ?? STATUS_STYLE.CANCELLED}`}>
      {status}
    </span>
  )
}

// ─── order card ───────────────────────────────────────────────────────────────

function OrderCard({ order, onCancelled }) {
  const [cancelling, setCancelling] = useState(false)

  const handleCancel = async () => {
    if (!window.confirm('Cancel this order?')) return
    setCancelling(true)
    try {
      await cancelOrder(order.id)
      onCancelled(order.id)
    } catch {
      setCancelling(false)
    }
  }

  const date = new Date(order.created_at).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  })

  const movies = order.movies ?? order.items ?? []
  const total  = Number(order.total_price ?? order.total_amount ?? 0)

  return (
    <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl overflow-hidden">
      {/* Header row */}
      <div className="flex flex-wrap items-center justify-between gap-3 px-5 py-4
        border-b border-[#2a2a38]">
        <div className="flex items-center gap-3">
          <span className="text-sm font-semibold text-[#f1f1f1]">
            Order #{order.id}
          </span>
          <StatusBadge status={order.status} />
        </div>
        <span className="text-xs text-[#55556a]">{date}</span>
      </div>

      {/* Movies list */}
      {movies.length > 0 && (
        <ul className="divide-y divide-[#2a2a38]">
          {movies.map((m) => (
            <li key={m.id} className="flex items-center justify-between px-5 py-3 gap-4">
              <Link
                to={`/movies/${m.id}`}
                className="text-sm text-[#9999aa] hover:text-white transition-colors
                  truncate max-w-[70%]"
              >
                {m.name}
              </Link>
              <span className="text-sm font-medium text-[#f1f1f1] shrink-0">
                ${Number(m.price).toFixed(2)}
              </span>
            </li>
          ))}
        </ul>
      )}

      {/* Footer row */}
      <div className="flex items-center justify-between px-5 py-4 border-t border-[#2a2a38]">
        <div className="text-sm">
          <span className="text-[#55556a]">Total </span>
          <span className="font-bold text-red-500">${total.toFixed(2)}</span>
        </div>

        {order.status === 'PENDING' && (
          <button
            onClick={handleCancel}
            disabled={cancelling}
            className="text-xs text-[#55556a] hover:text-red-400 transition-colors
              disabled:opacity-40"
          >
            {cancelling ? 'Cancelling…' : 'Cancel order'}
          </button>
        )}

        {order.status === 'PENDING' && order.payment_url && (
          <a
            href={order.payment_url}
            className="text-xs font-medium text-red-500 hover:text-red-400 transition-colors"
          >
            Complete payment →
          </a>
        )}
      </div>
    </div>
  )
}

// ─── skeleton ─────────────────────────────────────────────────────────────────

function OrderSkeleton() {
  return (
    <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl overflow-hidden animate-pulse">
      <div className="flex items-center justify-between px-5 py-4 border-b border-[#2a2a38]">
        <div className="h-4 w-24 bg-[#2a2a38] rounded" />
        <div className="h-3 w-20 bg-[#2a2a38] rounded" />
      </div>
      {[1, 2].map((i) => (
        <div key={i} className="flex items-center justify-between px-5 py-3 gap-4
          border-b border-[#2a2a38]">
          <div className="h-3 w-40 bg-[#2a2a38] rounded" />
          <div className="h-3 w-12 bg-[#2a2a38] rounded" />
        </div>
      ))}
      <div className="px-5 py-4">
        <div className="h-4 w-20 bg-[#2a2a38] rounded" />
      </div>
    </div>
  )
}

// ─── main page ────────────────────────────────────────────────────────────────

export default function Orders() {
  const [orders,  setOrders]  = useState([])
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  useEffect(() => {
    getMyOrders()
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : data?.items ?? []
        setOrders([...list].sort((a, b) => b.id - a.id))
      })
      .catch(() => setError('Failed to load orders. Please try again.'))
      .finally(() => setLoading(false))
  }, [])

  const handleCancelled = (orderId) => {
    setOrders((prev) =>
      prev.map((o) => o.id === orderId ? { ...o, status: 'CANCELLED' } : o)
    )
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      <h1 className="text-2xl font-bold text-[#f1f1f1]">My Orders</h1>

      {loading && (
        <div className="space-y-4">
          <OrderSkeleton /><OrderSkeleton />
        </div>
      )}

      {error && (
        <div className="bg-red-950/40 border border-red-800/40 rounded-xl px-4 py-3
          text-sm text-red-400">
          {error}
        </div>
      )}

      {!loading && !error && orders.length === 0 && (
        <div className="py-16 text-center space-y-4">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
            className="w-14 h-14 mx-auto text-[#2a2a38]">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9
              5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <div>
            <h2 className="text-lg font-semibold text-[#f1f1f1]">No orders yet</h2>
            <p className="text-sm text-[#55556a] mt-1">Your completed orders will appear here.</p>
          </div>
          <Link to="/"
            className="inline-block px-5 py-2 bg-red-600 hover:bg-red-500 text-white
              font-semibold rounded-xl text-sm transition-colors">
            Browse Movies
          </Link>
        </div>
      )}

      {!loading && !error && orders.length > 0 && (
        <div className="space-y-4">
          {orders.map((order) => (
            <OrderCard key={order.id} order={order} onCancelled={handleCancelled} />
          ))}
        </div>
      )}
    </div>
  )
}
