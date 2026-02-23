import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { activate } from '../api/auth'

export default function Activate() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')

  const [status, setStatus] = useState('idle') // idle | loading | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) return
    setStatus('loading')
    activate(token)
      .then(({ data }) => {
        setMessage(`Account for ${data.email} has been activated.`)
        setStatus('success')
      })
      .catch((err) => {
        const detail = err?.response?.data?.detail || 'Activation failed.'
        if (detail.toLowerCase().includes('already')) {
          setMessage('This account is already activated.')
          setStatus('success')
        } else {
          setMessage(detail)
          setStatus('error')
        }
      })
  }, [token])

  // ── no token in URL ───────────────────────────────────────────────────────
  if (!token) {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm text-center space-y-4">
          <p className="text-[#9999aa] text-sm">
            No activation token found. Check the link in your email.
          </p>
          <Link to="/login" className="text-sm text-red-500 hover:text-red-400 transition-colors">
            Back to Sign in
          </Link>
        </div>
      </div>
    )
  }

  // ── loading ───────────────────────────────────────────────────────────────
  if (status === 'idle' || status === 'loading') {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-10 h-10 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-[#55556a]">Activating your account…</p>
        </div>
      </div>
    )
  }

  // ── success ───────────────────────────────────────────────────────────────
  if (status === 'success') {
    return (
      <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
        <div className="w-full max-w-sm text-center space-y-6">
          <div className="w-16 h-16 mx-auto rounded-full bg-green-900/30 border border-green-700/40
            flex items-center justify-center">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
              className="w-8 h-8 text-green-500">
              <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div>
            <h2 className="text-xl font-bold text-[#f1f1f1]">You're all set!</h2>
            <p className="mt-2 text-sm text-[#9999aa]">{message}</p>
          </div>
          <Link to="/login"
            className="inline-block px-8 py-3 bg-red-600 hover:bg-red-500 text-white
              font-semibold rounded-xl text-sm transition-colors">
            Sign in
          </Link>
        </div>
      </div>
    )
  }

  // ── error ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm text-center space-y-6">
        <div className="w-16 h-16 mx-auto rounded-full bg-red-900/30 border border-red-700/40
          flex items-center justify-center">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            className="w-8 h-8 text-red-500">
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-bold text-[#f1f1f1]">Activation failed</h2>
          <p className="mt-2 text-sm text-[#9999aa]">{message}</p>
        </div>
        <div className="flex flex-col items-center gap-3">
          <Link to="/login"
            className="inline-block px-8 py-3 bg-red-600 hover:bg-red-500 text-white
              font-semibold rounded-xl text-sm transition-colors">
            Back to Sign in
          </Link>
          <p className="text-xs text-[#55556a]">
            If your link expired, register again to get a new one.
          </p>
        </div>
      </div>
    </div>
  )
}
