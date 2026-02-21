import { useState, useRef, useEffect } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

const FilmIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
    <path d="M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2zm0 2v12h16V6H4zm2 2h2v2H6V8zm0 4h2v2H6v-2zm0 4h2v2H6v-2zm10-8h2v2h-2V8zm0 4h2v2h-2v-2zm0 4h2v2h-2v-2z"/>
  </svg>
)

const CartIcon = ({ count }) => (
  <div className="relative">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-1.4 5.6A1 1 0 006.6 20H19" />
      <circle cx="9" cy="21" r="1" /><circle cx="19" cy="21" r="1" />
    </svg>
    {count > 0 && (
      <span className="absolute -top-2 -right-2 bg-red-600 text-white text-xs font-bold
        rounded-full min-w-[18px] h-[18px] flex items-center justify-center px-1 leading-none">
        {count > 99 ? '99+' : count}
      </span>
    )}
  </div>
)

const BellIcon = ({ hasUnread }) => (
  <div className="relative">
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
      className="w-6 h-6">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 00-9.33-4.997M9 17H4l1.405-1.405A2.032 2.032 0 006 14.158V11a6 6 0 0112 0v3.159c0 .538.214 1.055.595 1.436L20 17H9z" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M13.73 21a2 2 0 01-3.46 0" />
    </svg>
    {hasUnread && (
      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-[#0a0a0f]" />
    )}
  </div>
)

export default function Navbar({ cartCount = 0, hasUnread = false }) {
  const { user, isAuthenticated, logout } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [query, setQuery]     = useState(searchParams.get('search') || '')
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    const handler = (e) => {
      if (menuRef.current && !menuRef.current.contains(e.target)) setMenuOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const handleSearch = (e) => {
    e.preventDefault()
    const params = new URLSearchParams()
    if (query.trim()) params.set('search', query.trim())
    navigate(`/?${params.toString()}`)
  }

  const handleLogout = async () => {
    setMenuOpen(false)
    await logout()
    navigate('/login')
  }

  const initials = user?.email?.slice(0, 2).toUpperCase() ?? '?'

  return (
    <header className="sticky top-0 z-50 bg-[#0a0a0f]/90 backdrop-blur-md border-b border-[#2a2a38]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center gap-4">

        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 shrink-0 text-white hover:text-red-500 transition-colors">
          <FilmIcon />
          <span className="text-lg font-bold tracking-tight">
            Cinema<span className="text-red-600">Hub</span>
          </span>
        </Link>

        {/* Search */}
        <form onSubmit={handleSearch} className="flex-1 max-w-xl">
          <div className="relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search movies…"
              className="w-full bg-[#1a1a24] border border-[#2a2a38] rounded-lg pl-4 pr-10 py-2
                text-sm text-[#f1f1f1] placeholder-[#55556a]
                focus:outline-none focus:border-red-600 transition-colors"
            />
            <button type="submit"
              className="absolute right-2 top-1/2 -translate-y-1/2 text-[#55556a] hover:text-red-500 transition-colors">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
                <circle cx="11" cy="11" r="8" />
                <path strokeLinecap="round" d="M21 21l-4.35-4.35" />
              </svg>
            </button>
          </div>
        </form>

        {/* Right side */}
        <nav className="flex items-center gap-1 ml-auto shrink-0">
          <Link to="/"
            className="hidden sm:block px-3 py-1.5 text-sm text-[#9999aa] hover:text-white transition-colors rounded-lg hover:bg-white/5">
            Movies
          </Link>

          {isAuthenticated ? (
            <>
              {/* Cart */}
              <Link to="/cart"
                className="p-2 text-[#9999aa] hover:text-white transition-colors rounded-lg hover:bg-white/5">
                <CartIcon count={cartCount} />
              </Link>

              {/* Notifications */}
              <Link to="/profile#notifications"
                className="p-2 text-[#9999aa] hover:text-white transition-colors rounded-lg hover:bg-white/5">
                <BellIcon hasUnread={hasUnread} />
              </Link>

              {/* Avatar menu */}
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setMenuOpen((v) => !v)}
                  className="w-9 h-9 rounded-full bg-red-700 text-white text-sm font-bold
                    flex items-center justify-center hover:bg-red-600 transition-colors ml-1">
                  {initials}
                </button>

                {menuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-[#1a1a24] border border-[#2a2a38]
                    rounded-xl shadow-2xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-[#2a2a38]">
                      <p className="text-xs text-[#55556a]">Signed in as</p>
                      <p className="text-sm text-[#f1f1f1] truncate">{user?.email}</p>
                    </div>
                    <div className="py-1">
                      <MenuLink to="/profile" onClick={() => setMenuOpen(false)}>Profile</MenuLink>
                      <MenuLink to="/orders"  onClick={() => setMenuOpen(false)}>My Orders</MenuLink>
                    </div>
                    <div className="py-1 border-t border-[#2a2a38]">
                      <button onClick={handleLogout}
                        className="w-full text-left px-4 py-2 text-sm text-red-400
                          hover:bg-red-600/10 hover:text-red-300 transition-colors">
                        Sign out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login"
                className="px-3 py-1.5 text-sm text-[#9999aa] hover:text-white transition-colors rounded-lg hover:bg-white/5">
                Sign in
              </Link>
              <Link to="/register"
                className="px-4 py-1.5 text-sm font-medium bg-red-600 hover:bg-red-500
                  text-white rounded-lg transition-colors">
                Register
              </Link>
            </>
          )}
        </nav>
      </div>
    </header>
  )
}

function MenuLink({ to, onClick, children }) {
  return (
    <Link to={to} onClick={onClick}
      className="block px-4 py-2 text-sm text-[#f1f1f1] hover:bg-white/5 transition-colors">
      {children}
    </Link>
  )
}
