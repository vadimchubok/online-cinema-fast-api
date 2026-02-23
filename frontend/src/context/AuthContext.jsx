import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { login as apiLogin, logout as apiLogout, getMe } from '../api/auth'
import { saveTokens, clearTokens, getAccessToken } from '../api/client'
import { clearLocalCartItems } from '../api/cart'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser]       = useState(null)   // { id, email, is_active, user_group }
  const [loading, setLoading] = useState(true)   // true while restoring session on mount

  // ─── restore session on first load ────────────────────────────────────────
  useEffect(() => {
    const token = getAccessToken()
    if (!token) {
      setLoading(false)
      return
    }

    getMe()
      .then(({ data }) => setUser(data))
      .catch(() => {
        // token expired and refresh also failed (client interceptor already
        // cleared storage) — just ensure state is clean
        clearTokens()
        setUser(null)
      })
      .finally(() => setLoading(false))
  }, [])

  // ─── login ────────────────────────────────────────────────────────────────
  const login = useCallback(async (email, password) => {
    const { data: tokens } = await apiLogin(email, password)
    saveTokens(tokens)

    const { data: me } = await getMe()
    setUser(me)

    return me   // caller can redirect based on user_group
  }, [])

  // ─── logout ───────────────────────────────────────────────────────────────
  const logout = useCallback(async () => {
    try {
      await apiLogout()
    } catch {
      // best-effort — clear local state regardless
    } finally {
      clearTokens()
      clearLocalCartItems()
      setUser(null)
    }
  }, [])

  // ─── helpers ──────────────────────────────────────────────────────────────
  const isAuthenticated = Boolean(user)
  const isModerator = user?.user_group === 'MODERATOR' || user?.user_group === 'ADMIN'
  const isAdmin     = user?.user_group === 'ADMIN'

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, isModerator, isAdmin, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}
