import { useEffect } from 'react'
import { Link } from 'react-router-dom'
import { clearLocalCartItems, localCartCount } from '../api/cart'

export default function PaymentSuccess() {
  // Clear local cart on first render — Stripe webhook already marked order paid
  useEffect(() => {
    const count = localCartCount()
    if (count > 0) {
      clearLocalCartItems()
      window.dispatchEvent(new CustomEvent('cinemahub:cart', { detail: { delta: -count } }))
    }
  }, [])

  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 py-20 text-center space-y-6">
      {/* Animated checkmark */}
      <div className="mx-auto w-20 h-20 rounded-full bg-green-950/60 border border-green-700/40
        flex items-center justify-center">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          className="w-10 h-10 text-green-400">
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-[#f1f1f1]">Payment Successful!</h1>
        <p className="text-sm text-[#9999aa]">
          Your order has been confirmed. You now have access to your purchased movies.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          to="/orders"
          className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold
            rounded-xl text-sm transition-colors"
        >
          View My Orders
        </Link>
        <Link
          to="/"
          className="px-6 py-2.5 bg-[#1a1a24] hover:bg-[#2a2a38] text-[#9999aa]
            hover:text-[#f1f1f1] font-semibold rounded-xl text-sm transition-colors
            border border-[#2a2a38]"
        >
          Browse More Movies
        </Link>
      </div>
    </div>
  )
}
