import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { register } from '../api/auth'

// Password rules mirrored from backend validators.py
const RULES = [
  { label: 'At least 8 characters',      test: (p) => p.length >= 8 },
  { label: 'One uppercase letter',        test: (p) => /[A-Z]/.test(p) },
  { label: 'One lowercase letter',        test: (p) => /[a-z]/.test(p) },
  { label: 'One digit',                   test: (p) => /\d/.test(p) },
  { label: 'One special char (@$!%*?#&)', test: (p) => /[@$!%*?#&]/.test(p) },
]

function StrengthHints({ password }) {
  if (!password) return null
  return (
    <ul className="mt-2 space-y-1">
      {RULES.map((r) => {
        const ok = r.test(password)
        return (
          <li key={r.label} className={`flex items-center gap-1.5 text-[11px]
            ${ok ? 'text-green-500' : 'text-[#55556a]'}`}>
            <span>{ok ? '✓' : '○'}</span>
            {r.label}
          </li>
        )
      })}
    </ul>
  )
}

function EyeIcon({ open }) {
  return open ? (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274
          4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97
          9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242
          4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0
          0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0
          01-4.132 5.411m0 0L21 21" />
    </svg>
  )
}

export default function Register() {
  const navigate = useNavigate()

  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [confirm,  setConfirm]  = useState('')
  const [showPw,   setShowPw]   = useState(false)
  const [error,    setError]    = useState(null)
  const [loading,  setLoading]  = useState(false)
  const [success,  setSuccess]  = useState(false)

  const allRulesPass = RULES.every((r) => r.test(password))
  const passwordsMatch = password === confirm

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    if (!allRulesPass) { setError('Password does not meet the requirements below.'); return }
    if (!passwordsMatch) { setError('Passwords do not match.'); return }

    setLoading(true)
    try {
      await register(email.trim(), password)
      setSuccess(true)
    } catch (err) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  // ── success state ─────────────────────────────────────────────────────────
  if (success) {
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
            <h2 className="text-xl font-bold text-[#f1f1f1]">Account created!</h2>
            <p className="mt-2 text-sm text-[#9999aa]">
              We sent an activation link to{' '}
              <span className="text-[#f1f1f1] font-medium">{email}</span>.
              Click the link in the email to activate your account.
            </p>
          </div>
          <Link to="/login"
            className="inline-block px-6 py-2.5 bg-red-600 hover:bg-red-500 text-white
              font-semibold rounded-xl text-sm transition-colors">
            Go to Sign in
          </Link>
        </div>
      </div>
    )
  }

  // ── form ─────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-[calc(100vh-8rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-sm">

        {/* Logo */}
        <div className="text-center mb-8">
          <Link to="/" className="text-2xl font-bold text-white">
            Cinema<span className="text-red-600">Hub</span>
          </Link>
          <p className="mt-2 text-sm text-[#55556a]">Create your account</p>
        </div>

        {/* Card */}
        <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl p-8 space-y-5">

          {error && (
            <div className="bg-red-950/40 border border-red-800/40 rounded-xl px-4 py-3
              text-sm text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Email */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-[#9999aa] uppercase tracking-wider">
                Email
              </label>
              <input
                type="email" required autoComplete="email" autoFocus
                value={email} onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-[#1a1a24] border border-[#2a2a38] rounded-xl px-4 py-3
                  text-sm text-[#f1f1f1] placeholder-[#55556a]
                  focus:outline-none focus:border-red-600 transition-colors"
              />
            </div>

            {/* Password */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-[#9999aa] uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'} required autoComplete="new-password"
                  value={password} onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full bg-[#1a1a24] border border-[#2a2a38] rounded-xl px-4 py-3 pr-11
                    text-sm text-[#f1f1f1] placeholder-[#55556a]
                    focus:outline-none focus:border-red-600 transition-colors"
                />
                <button type="button" onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#55556a]
                    hover:text-[#9999aa] transition-colors">
                  <EyeIcon open={showPw} />
                </button>
              </div>
              <StrengthHints password={password} />
            </div>

            {/* Confirm */}
            <div className="space-y-1.5">
              <label className="block text-xs font-medium text-[#9999aa] uppercase tracking-wider">
                Confirm Password
              </label>
              <input
                type={showPw ? 'text' : 'password'} required autoComplete="new-password"
                value={confirm} onChange={(e) => setConfirm(e.target.value)}
                placeholder="••••••••"
                className={`w-full bg-[#1a1a24] border rounded-xl px-4 py-3
                  text-sm text-[#f1f1f1] placeholder-[#55556a]
                  focus:outline-none transition-colors
                  ${confirm && !passwordsMatch
                    ? 'border-red-700 focus:border-red-500'
                    : 'border-[#2a2a38] focus:border-red-600'}`}
              />
              {confirm && !passwordsMatch && (
                <p className="text-[11px] text-red-400">Passwords don't match.</p>
              )}
            </div>

            <button type="submit" disabled={loading}
              className="w-full py-3 bg-red-600 hover:bg-red-500 disabled:opacity-60
                disabled:cursor-not-allowed text-white font-semibold rounded-xl
                transition-colors text-sm mt-2">
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>
        </div>

        <p className="text-center text-sm text-[#55556a] mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-red-500 hover:text-red-400 transition-colors font-medium">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
