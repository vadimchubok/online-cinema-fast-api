import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  removeFromCart, clearCart,
  getLocalCartItems, removeLocalCartItem, clearLocalCartItems, localCartCount,
} from '../api/cart'
import { createOrder } from '../api/orders'

const HUES = [0, 25, 200, 260, 290, 340, 160, 220]
function posterStyle(id) {
  const hue = HUES[id % HUES.length]
  return { background: `linear-gradient(160deg, hsl(${hue} 55% 11%) 0%, hsl(${hue} 25% 5%) 100%)` }
}

// ─── single cart row ──────────────────────────────────────────────────────────

function CartRow({ movie, onRemove }) {
  const [removing, setRemoving] = useState(false)

  const handleRemove = async () => {
    setRemoving(true)
    try {
      await removeFromCart(movie.id)
      removeLocalCartItem(movie.id)
      window.dispatchEvent(new CustomEvent('cinemahub:cart', { detail: { delta: -1 } }))
      onRemove(movie.id)
    } catch {
      setRemoving(false)
    }
  }

  return (
    <div className="flex items-center gap-4 py-4 border-b border-[#2a2a38] last:border-0">
      {/* Mini poster */}
      <Link to={`/movies/${movie.id}`}
        className="shrink-0 w-14 h-20 rounded-lg overflow-hidden border border-[#2a2a38]
          hover:border-red-600/40 transition-colors"
        style={posterStyle(movie.id)}
      />

      {/* Info */}
      <div className="flex-1 min-w-0">
        <Link to={`/movies/${movie.id}`}
          className="font-medium text-[#f1f1f1] hover:text-white transition-colors
            text-sm line-clamp-2 leading-snug">
          {movie.name}
        </Link>
        <div className="flex flex-wrap items-center gap-1.5 mt-1">
          <span className="text-xs text-[#55556a]">{movie.year}</span>
          {movie.genres?.slice(0, 2).map((g) => (
            <span key={g.id || g.name}
              className="text-[10px] px-1.5 py-0.5 rounded bg-[#1a1a24] text-[#9999aa]
                border border-[#2a2a38]">
              {g.name}
            </span>
          ))}
        </div>
      </div>

      {/* Price + remove */}
      <div className="flex flex-col items-end gap-2 shrink-0">
        <span className="font-bold text-red-500 text-sm">
          ${Number(movie.price).toFixed(2)}
        </span>
        <button
          onClick={handleRemove}
          disabled={removing}
          className="text-[11px] text-[#55556a] hover:text-red-400 transition-colors
            disabled:opacity-40"
        >
          {removing ? 'Removing…' : 'Remove'}
        </button>
      </div>
    </div>
  )
}

// ─── main page ────────────────────────────────────────────────────────────────

export default function Cart({ setCartCount }) {
  const navigate = useNavigate()
  const [items,     setItems]     = useState(() => getLocalCartItems())
  const [clearing,  setClearing]  = useState(false)
  const [ordering,  setOrdering]  = useState(false)
  const [orderError, setOrderError] = useState(null)

  // Sync Navbar badge on mount from localStorage
  useEffect(() => {
    setCartCount?.(localCartCount())
  }, [setCartCount])

  const total = items.reduce((sum, m) => sum + Number(m.price), 0)

  const handleRemoved = (movieId) => {
    setItems((prev) => {
      const next = prev.filter((m) => m.id !== movieId)
      setCartCount?.(next.length)
      return next
    })
  }

  const handleClear = async () => {
    if (!window.confirm('Remove all items from your cart?')) return
    setClearing(true)
    try {
      await clearCart()
    } catch {
      // backend throws if cart is empty or doesn't exist — still clear locally
    } finally {
      clearLocalCartItems()
      window.dispatchEvent(new CustomEvent('cinemahub:cart', { detail: { delta: -items.length } }))
      setItems([])
      setCartCount?.(0)
      setClearing(false)
    }
  }

  const handleCheckout = async () => {
    setOrdering(true)
    setOrderError(null)
    try {
      const { data } = await createOrder()
      // Backend returns payment_url — redirect to Stripe checkout
      if (data.payment_url) {
        // Clear local cart now; Stripe webhook will mark the order paid
        clearLocalCartItems()
        setCartCount?.(0)
        window.location.href = data.payment_url
      } else {
        navigate('/orders')
      }
    } catch (err) {
      const detail = err?.response?.data?.detail
      setOrderError(detail || 'Failed to create order. Please try again.')
      setOrdering(false)
    }
  }

  // ── empty state ──────────────────────────────────────────────────────────
  if (items.length === 0) {
    return (
      <div className="max-w-2xl mx-auto px-4 sm:px-6 py-16 text-center space-y-6">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
          className="w-16 h-16 mx-auto text-[#2a2a38]">
          <path strokeLinecap="round" strokeLinejoin="round"
            d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-1.4 5.6A1 1 0 006.6
              20H19m-10 0a1 1 0 100 2 1 1 0 000-2zm10 0a1 1 0 100 2 1 1 0 000-2z" />
        </svg>
        <div>
          <h2 className="text-xl font-bold text-[#f1f1f1]">Your cart is empty</h2>
          <p className="text-sm text-[#55556a] mt-1">
            Browse movies and add them to your cart.
          </p>
        </div>
        <Link to="/"
          className="inline-block px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white
            font-semibold rounded-xl text-sm transition-colors">
          Browse Movies
        </Link>
      </div>
    )
  }

  // ── cart with items ───────────────────────────────────────────────────────
  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6">

      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-[#f1f1f1]">
          Cart
          <span className="ml-2 text-base font-normal text-[#55556a]">
            ({items.length} {items.length === 1 ? 'item' : 'items'})
          </span>
        </h1>
        <button
          onClick={handleClear}
          disabled={clearing}
          className="text-sm text-[#55556a] hover:text-red-400 transition-colors
            disabled:opacity-40"
        >
          {clearing ? 'Clearing…' : 'Clear all'}
        </button>
      </div>

      {/* Item list */}
      <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl px-5">
        {items.map((movie) => (
          <CartRow key={movie.id} movie={movie} onRemove={handleRemoved} />
        ))}
      </div>

      {/* Order summary */}
      <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl p-6 space-y-4">
        <h2 className="text-sm font-semibold text-[#f1f1f1] uppercase tracking-wider">
          Order Summary
        </h2>

        <div className="space-y-2 text-sm">
          {items.map((m) => (
            <div key={m.id} className="flex justify-between text-[#9999aa]">
              <span className="truncate pr-4 max-w-[70%]">{m.name}</span>
              <span className="shrink-0">${Number(m.price).toFixed(2)}</span>
            </div>
          ))}
        </div>

        <div className="border-t border-[#2a2a38] pt-3 flex justify-between items-center">
          <span className="font-semibold text-[#f1f1f1]">Total</span>
          <span className="text-xl font-bold text-red-500">${total.toFixed(2)}</span>
        </div>

        {orderError && (
          <div className="bg-red-950/40 border border-red-800/40 rounded-xl px-4 py-3
            text-sm text-red-400">
            {orderError}
          </div>
        )}

        <button
          onClick={handleCheckout}
          disabled={ordering}
          className="w-full py-3 bg-red-600 hover:bg-red-500 disabled:opacity-60
            disabled:cursor-wait text-white font-semibold rounded-xl transition-colors text-sm"
        >
          {ordering ? 'Creating order…' : 'Proceed to Checkout →'}
        </button>

        <p className="text-center text-xs text-[#55556a]">
          You'll be redirected to Stripe to complete payment securely.
        </p>
      </div>
    </div>
  )
}
