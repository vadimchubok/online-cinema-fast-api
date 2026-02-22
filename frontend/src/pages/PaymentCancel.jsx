import { Link } from 'react-router-dom'

export default function PaymentCancel() {
  return (
    <div className="max-w-md mx-auto px-4 sm:px-6 py-20 text-center space-y-6">
      {/* X icon */}
      <div className="mx-auto w-20 h-20 rounded-full bg-red-950/60 border border-red-800/40
        flex items-center justify-center">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
          className="w-10 h-10 text-red-400">
          <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-bold text-[#f1f1f1]">Payment Cancelled</h1>
        <p className="text-sm text-[#9999aa]">
          No charge was made. Your cart items are still saved — you can complete
          your purchase whenever you're ready.
        </p>
      </div>

      <div className="flex flex-col sm:flex-row gap-3 justify-center">
        <Link
          to="/cart"
          className="px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white font-semibold
            rounded-xl text-sm transition-colors"
        >
          Back to Cart
        </Link>
        <Link
          to="/"
          className="px-6 py-2.5 bg-[#1a1a24] hover:bg-[#2a2a38] text-[#9999aa]
            hover:text-[#f1f1f1] font-semibold rounded-xl text-sm transition-colors
            border border-[#2a2a38]"
        >
          Browse Movies
        </Link>
      </div>
    </div>
  )
}
