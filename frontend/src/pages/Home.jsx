import { useState, useEffect, useCallback } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { getMovies, getGenres } from '../api/movies'
import MovieCard from '../components/movies/MovieCard'
import Pagination from '../components/ui/Pagination'
import { useAuth } from '../context/AuthContext'

const LIMIT = 20

const SORT_OPTIONS = [
  { value: '',            label: 'Relevance' },
  { value: 'popularity', label: 'Most Popular' },
  { value: 'year_desc',  label: 'Newest First' },
  { value: 'price_asc',  label: 'Price: Low → High' },
  { value: 'price_desc', label: 'Price: High → Low' },
]

// ─── guest landing ────────────────────────────────────────────────────────────
function GuestHero() {
  return (
    <div className="flex flex-col items-center justify-center text-center px-4 py-28 gap-8">
      {/* Glow backdrop */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2
          w-[600px] h-[400px] bg-red-900/10 rounded-full blur-3xl" />
      </div>

      <div className="relative space-y-4 max-w-xl">
        <h1 className="text-5xl font-bold text-white leading-tight">
          Your Cinema,<br />
          <span className="text-red-600">Anytime.</span>
        </h1>
        <p className="text-[#9999aa] text-lg">
          Thousands of movies. One subscription. Sign in to start watching.
        </p>
      </div>

      <div className="relative flex flex-col sm:flex-row gap-3">
        <Link to="/register"
          className="px-8 py-3 bg-red-600 hover:bg-red-500 text-white font-semibold
            rounded-xl transition-colors text-sm">
          Get Started
        </Link>
        <Link to="/login"
          className="px-8 py-3 bg-[#1a1a24] hover:bg-[#2a2a38] text-[#f1f1f1]
            border border-[#2a2a38] font-semibold rounded-xl transition-colors text-sm">
          Sign In
        </Link>
      </div>
    </div>
  )
}

// ─── skeleton card ────────────────────────────────────────────────────────────
function SkeletonCard() {
  return (
    <div className="rounded-xl overflow-hidden border border-[#2a2a38] bg-[#16161f] animate-pulse">
      <div className="aspect-[2/3] bg-[#1a1a24]" />
      <div className="p-3 space-y-2">
        <div className="h-2.5 w-16 rounded bg-[#2a2a38]" />
        <div className="h-3.5 w-full rounded bg-[#2a2a38]" />
        <div className="h-3.5 w-3/4 rounded bg-[#2a2a38]" />
        <div className="h-2.5 w-24 rounded bg-[#2a2a38] mt-1" />
        <div className="flex justify-between items-center pt-1">
          <div className="h-4 w-12 rounded bg-[#2a2a38]" />
          <div className="h-7 w-24 rounded-lg bg-[#2a2a38]" />
        </div>
      </div>
    </div>
  )
}

// ─── genre chip bar ───────────────────────────────────────────────────────────
function GenreBar({ genres, activeId, onChange }) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1" style={{ scrollbarWidth: 'none' }}>
      <Chip active={!activeId} onClick={() => onChange(null)}>All</Chip>
      {genres.map((g) => (
        <Chip key={g.id} active={activeId === g.id} onClick={() => onChange(g.id)}>
          {g.name}
          <span className="ml-1 opacity-50 text-[10px]">{g.movie_count}</span>
        </Chip>
      ))}
    </div>
  )
}

function Chip({ active, onClick, children }) {
  return (
    <button
      onClick={onClick}
      className={`shrink-0 px-3 py-1.5 rounded-full text-xs font-medium transition-colors whitespace-nowrap
        ${active
          ? 'bg-red-600 text-white'
          : 'bg-[#1a1a24] text-[#9999aa] border border-[#2a2a38] hover:border-red-600/50 hover:text-white'
        }`}
    >
      {children}
    </button>
  )
}

// ─── main page ────────────────────────────────────────────────────────────────
export default function Home() {
  const { isAuthenticated, loading: authLoading } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()

  const search  = searchParams.get('search')   || ''
  const sortBy  = searchParams.get('sort_by')  || ''
  const genreId = searchParams.get('genre_id') ? Number(searchParams.get('genre_id')) : null
  const page    = searchParams.get('page')     ? Number(searchParams.get('page')) : 1

  const [genres,  setGenres]  = useState([])
  const [movies,  setMovies]  = useState([])
  const [total,   setTotal]   = useState(0)
  const [loading, setLoading] = useState(true)
  const [error,   setError]   = useState(null)

  // Only fetch when authenticated
  useEffect(() => {
    if (!isAuthenticated) return
    getGenres()
      .then(({ data }) => setGenres(data))
      .catch(() => {})
  }, [isAuthenticated])

  const fetchMovies = useCallback(() => {
    if (!isAuthenticated) return
    setLoading(true)
    setError(null)

    const params = {
      skip:  (page - 1) * LIMIT,
      limit: LIMIT,
      ...(search  && { search }),
      ...(sortBy  && { sort_by: sortBy }),
      ...(genreId && { genre_id: genreId }),
    }

    getMovies(params)
      .then(({ data }) => {
        setMovies(data.items ?? [])
        setTotal(data.total  ?? 0)
      })
      .catch(() => setError('Failed to load movies. Please try again.'))
      .finally(() => setLoading(false))
  }, [isAuthenticated, search, sortBy, genreId, page])

  useEffect(() => { fetchMovies() }, [fetchMovies])

  const totalPages = Math.ceil(total / LIMIT)

  function setParam(key, value) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (value != null && value !== '') next.set(key, value)
      else next.delete(key)
      next.delete('page')
      return next
    })
  }

  function handlePageChange(p) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      if (p > 1) next.set('page', p)
      else next.delete('page')
      return next
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  // Wait for auth to resolve before deciding which view to show
  if (authLoading) return null

  // Guest view
  if (!isAuthenticated) return <GuestHero />

  // Authenticated view
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 space-y-6">

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-[#f1f1f1]">
            {search ? `Results for "${search}"` : 'Browse Movies'}
          </h1>
          {!loading && (
            <p className="text-sm text-[#55556a] mt-0.5">
              {total.toLocaleString()} {total === 1 ? 'movie' : 'movies'}
            </p>
          )}
        </div>

        {/* Sort */}
        <select
          value={sortBy}
          onChange={(e) => setParam('sort_by', e.target.value)}
          className="bg-[#1a1a24] border border-[#2a2a38] rounded-lg px-3 py-2 text-sm
            text-[#f1f1f1] focus:outline-none focus:border-red-600 transition-colors
            cursor-pointer self-start sm:self-auto"
        >
          {SORT_OPTIONS.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      </div>

      {/* Genre chips */}
      {genres.length > 0 && (
        <GenreBar
          genres={genres}
          activeId={genreId}
          onChange={(id) => setParam('genre_id', id)}
        />
      )}

      {/* Error */}
      {error && (
        <div className="rounded-xl border border-red-800/40 bg-red-950/20 px-4 py-3 text-sm text-red-400">
          {error}{' '}
          <button onClick={fetchMovies} className="underline hover:no-underline">Retry</button>
        </div>
      )}

      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-5 gap-4">
        {loading
          ? Array.from({ length: LIMIT }, (_, i) => <SkeletonCard key={i} />)
          : movies.map((m) => <MovieCard key={m.id} movie={m} />)
        }
      </div>

      {/* Empty */}
      {!loading && movies.length === 0 && !error && (
        <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"
            className="w-12 h-12 text-[#2a2a38]">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5
                18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0
                002.25 7.5v9A2.25 2.25 0 004.5 18.75z" />
          </svg>
          <p className="text-[#9999aa] text-sm">No movies found.</p>
          {(search || genreId || sortBy) && (
            <button
              onClick={() => setSearchParams({})}
              className="text-xs text-red-500 hover:text-red-400 transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>
      )}

      {/* Pagination */}
      <Pagination page={page} totalPages={totalPages} onChange={handlePageChange} />
    </div>
  )
}
