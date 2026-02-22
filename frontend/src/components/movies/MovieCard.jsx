import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { addToCart, addLocalCartItem } from '../../api/cart'
import { useAuth } from '../../context/AuthContext'

// Deterministic poster gradient from movie id
const HUES = [0, 25, 200, 260, 290, 340, 160, 220]

function posterStyle(id) {
  const hue = HUES[id % HUES.length]
  return {
    background: `linear-gradient(160deg, hsl(${hue} 55% 11%) 0%, hsl(${hue} 25% 5%) 100%)`,
  }
}

function StarIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969
        0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755
        1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1
        1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  )
}

function CartPlusIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
      <path strokeLinecap="round" strokeLinejoin="round"
        d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-1.4 5.6A1 1 0 006.6 20H19" />
      <circle cx="9" cy="21" r="1" /><circle cx="19" cy="21" r="1" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m2-2H10" />
    </svg>
  )
}

export default function MovieCard({ movie, onAdded }) {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus] = useState('idle') // idle | adding | added | error

  const handleAddToCart = async (e) => {
    e.preventDefault()
    if (!isAuthenticated) { navigate('/login'); return }
    if (status === 'adding' || status === 'added') return

    setStatus('adding')
    try {
      await addToCart(movie.id)
      addLocalCartItem(movie)
      setStatus('added')
      window.dispatchEvent(new CustomEvent('cinemahub:cart', { detail: { delta: 1 } }))
      onAdded?.()
      setTimeout(() => setStatus('idle'), 2000)
    } catch {
      setStatus('error')
      setTimeout(() => setStatus('idle'), 2000)
    }
  }

  const primaryGenre = movie.genres?.[0]?.name ?? ''

  const btnLabel = { idle: 'Add to Cart', adding: 'Adding…', added: 'Added!', error: 'Failed' }
  const btnClass = {
    idle:   'bg-red-600 hover:bg-red-500 text-white',
    adding: 'bg-red-800 text-red-300 cursor-wait',
    added:  'bg-green-700 text-green-100 cursor-default',
    error:  'bg-zinc-700 text-zinc-300 cursor-default',
  }

  return (
    <Link
      to={`/movies/${movie.id}`}
      className="group relative flex flex-col rounded-xl overflow-hidden border border-[#2a2a38]
        bg-[#16161f] hover:border-red-600/50 transition-all duration-300 hover:-translate-y-0.5
        hover:shadow-2xl hover:shadow-red-950/30"
    >
      {/* Poster */}
      <div
        className="relative aspect-[2/3] overflow-hidden"
        style={posterStyle(movie.id)}
      >
        {/* Certification badge */}
        {movie.certification && (
          <span className="absolute top-2 left-2 px-1.5 py-0.5 text-[10px] font-bold
            bg-black/60 text-[#9999aa] rounded border border-[#2a2a38] backdrop-blur-sm">
            {movie.certification.name}
          </span>
        )}

        {/* Genre watermark */}
        {primaryGenre && (
          <span className="absolute bottom-3 left-1/2 -translate-x-1/2
            text-[11px] font-medium tracking-widest uppercase text-white/20 whitespace-nowrap">
            {primaryGenre}
          </span>
        )}

        {/* Title overlay on hover */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent
          opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end p-3">
          <p className="text-xs text-[#9999aa] line-clamp-3">{movie.description}</p>
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-col flex-1 p-3 gap-2">
        {/* Genres */}
        {movie.genres?.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {movie.genres.slice(0, 2).map((g) => (
              <span key={g.id}
                className="text-[10px] px-1.5 py-0.5 rounded bg-[#1a1a24] text-[#9999aa] border border-[#2a2a38]">
                {g.name}
              </span>
            ))}
          </div>
        )}

        {/* Title */}
        <h3 className="text-sm font-semibold text-[#f1f1f1] line-clamp-2 leading-snug group-hover:text-white transition-colors">
          {movie.name}
        </h3>

        {/* Meta row */}
        <div className="flex items-center gap-2 text-xs text-[#55556a]">
          <span>{movie.year}</span>
          <span>·</span>
          <span>{movie.time}m</span>
          {movie.imdb && (
            <>
              <span>·</span>
              <span className="flex items-center gap-0.5 text-[#f5c518]">
                <StarIcon />
                {movie.imdb.toFixed(1)}
              </span>
            </>
          )}
        </div>

        {/* Price + CTA */}
        <div className="mt-auto pt-2 flex items-center justify-between gap-2">
          <span className="text-base font-bold text-red-500">
            ${Number(movie.price).toFixed(2)}
          </span>
          <button
            onClick={handleAddToCart}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-xs font-medium
              transition-all duration-200 ${btnClass[status]}`}
          >
            {status === 'idle' && <CartPlusIcon />}
            {btnLabel[status]}
          </button>
        </div>
      </div>
    </Link>
  )
}
