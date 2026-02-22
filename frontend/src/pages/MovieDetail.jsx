import { useState, useEffect, useCallback } from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { getMovie } from '../api/movies'
import {
  getReactions, setReaction, removeReaction,
  getRating, setRating, removeRating,
  getComments, createComment, deleteComment,
} from '../api/interactions'
import { addToCart } from '../api/cart'
import { useAuth } from '../context/AuthContext'
import Spinner from '../components/ui/Spinner'

// ─── helpers ─────────────────────────────────────────────────────────────────

const HUES = [0, 25, 200, 260, 290, 340, 160, 220]
function posterStyle(id) {
  const hue = HUES[id % HUES.length]
  return {
    background: `linear-gradient(160deg, hsl(${hue} 55% 13%) 0%, hsl(${hue} 25% 5%) 100%)`,
  }
}

function fmt(n) {
  if (!n) return '—'
  return Number(n).toLocaleString()
}

function timeStr(mins) {
  if (!mins) return ''
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return h ? `${h}h ${m}m` : `${m}m`
}

function relativeTime(iso) {
  const diff = Date.now() - new Date(iso).getTime()
  const mins = Math.floor(diff / 60000)
  if (mins < 1)  return 'just now'
  if (mins < 60) return `${mins}m ago`
  const hrs = Math.floor(mins / 60)
  if (hrs < 24)  return `${hrs}h ago`
  const days = Math.floor(hrs / 24)
  if (days < 30) return `${days}d ago`
  return new Date(iso).toLocaleDateString()
}

// ─── add to cart button ───────────────────────────────────────────────────────

function AddToCartButton({ movieId }) {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const [status, setStatus] = useState('idle')

  const handleClick = async () => {
    if (!isAuthenticated) { navigate('/login'); return }
    if (status !== 'idle') return
    setStatus('adding')
    try {
      await addToCart(movieId)
      setStatus('added')
      window.dispatchEvent(new CustomEvent('cinemahub:cart', { detail: { delta: 1 } }))
      setTimeout(() => setStatus('idle'), 2500)
    } catch (err) {
      const msg = err?.response?.data?.detail
      setStatus(msg?.toLowerCase().includes('already') ? 'owned' : 'error')
      setTimeout(() => setStatus('idle'), 2500)
    }
  }

  const map = {
    idle:   { label: 'Add to Cart',   cls: 'bg-red-600 hover:bg-red-500 text-white' },
    adding: { label: 'Adding…',       cls: 'bg-red-800 text-red-300 cursor-wait' },
    added:  { label: '✓ Added!',      cls: 'bg-green-700 text-green-100' },
    owned:  { label: 'Already owned', cls: 'bg-zinc-700 text-zinc-300 cursor-default' },
    error:  { label: 'Failed — retry',cls: 'bg-zinc-700 text-zinc-300' },
  }
  const { label, cls } = map[status]

  return (
    <button onClick={handleClick}
      className={`w-full sm:w-auto px-8 py-3 rounded-xl font-semibold text-sm
        transition-all duration-200 ${cls}`}>
      {label}
    </button>
  )
}

// ─── reactions bar ────────────────────────────────────────────────────────────

function ReactionsBar({ movieId }) {
  const { isAuthenticated } = useAuth()
  const [data, setData]       = useState(null)  // { likes, dislikes, my_reaction }
  const [loading, setLoading] = useState(true)
  const [busy, setBusy]       = useState(false)

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return }
    getReactions(movieId)
      .then(({ data }) => setData(data))
      .finally(() => setLoading(false))
  }, [movieId, isAuthenticated])

  const handleReact = async (reaction) => {
    if (busy || !isAuthenticated) return
    setBusy(true)
    try {
      if (data?.my_reaction === reaction) {
        await removeReaction(movieId)
        setData((d) => ({ ...d, my_reaction: null, [reaction === 'LIKE' ? 'likes' : 'dislikes']: d[reaction === 'LIKE' ? 'likes' : 'dislikes'] - 1 }))
      } else {
        await setReaction(movieId, reaction)
        // optimistic update
        setData((d) => {
          const wasLike    = d.my_reaction === 'LIKE'
          const wasDislike = d.my_reaction === 'DISLIKE'
          return {
            ...d,
            my_reaction: reaction,
            likes:    reaction === 'LIKE'    ? d.likes    + 1 : wasLike    ? d.likes    - 1 : d.likes,
            dislikes: reaction === 'DISLIKE' ? d.dislikes + 1 : wasDislike ? d.dislikes - 1 : d.dislikes,
          }
        })
      }
    } finally {
      setBusy(false)
    }
  }

  if (!isAuthenticated) return (
    <AuthPrompt text="Sign in to react" />
  )

  if (loading) return <div className="h-10 w-40 rounded-xl bg-[#1a1a24] animate-pulse" />

  return (
    <div className="flex items-center gap-3">
      <ReactionBtn
        icon="👍" label="Like" count={data?.likes ?? 0}
        active={data?.my_reaction === 'LIKE'}
        onClick={() => handleReact('LIKE')}
      />
      <ReactionBtn
        icon="👎" label="Dislike" count={data?.dislikes ?? 0}
        active={data?.my_reaction === 'DISLIKE'}
        onClick={() => handleReact('DISLIKE')}
      />
    </div>
  )
}

function ReactionBtn({ icon, label, count, active, onClick }) {
  return (
    <button onClick={onClick}
      title={label}
      className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium
        border transition-all duration-150
        ${active
          ? 'bg-red-600/20 border-red-500 text-red-400'
          : 'bg-[#1a1a24] border-[#2a2a38] text-[#9999aa] hover:border-red-600/40 hover:text-white'
        }`}>
      <span className="text-base leading-none">{icon}</span>
      <span>{fmt(count)}</span>
    </button>
  )
}

// ─── rating widget ────────────────────────────────────────────────────────────

function RatingWidget({ movieId }) {
  const { isAuthenticated } = useAuth()
  const [summary, setSummary] = useState(null)  // { average_score, votes, my_score }
  const [loading, setLoading] = useState(true)
  const [hover, setHover]     = useState(null)
  const [busy, setBusy]       = useState(false)

  useEffect(() => {
    if (!isAuthenticated) { setLoading(false); return }
    getRating(movieId)
      .then(({ data }) => setSummary(data))
      .finally(() => setLoading(false))
  }, [movieId, isAuthenticated])

  const handleRate = async (score) => {
    if (busy || !isAuthenticated) return
    setBusy(true)
    try {
      if (summary?.my_score === score) {
        await removeRating(movieId)
        setSummary((s) => ({ ...s, my_score: null }))
      } else {
        await setRating(movieId, score)
        setSummary((s) => ({ ...s, my_score: score }))
      }
    } finally {
      setBusy(false)
    }
  }

  if (!isAuthenticated) return <AuthPrompt text="Sign in to rate" />
  if (loading) return <div className="h-10 w-64 rounded-xl bg-[#1a1a24] animate-pulse" />

  const active  = hover ?? summary?.my_score

  return (
    <div className="space-y-2">
      {summary?.average_score != null && (
        <p className="text-xs text-[#55556a]">
          Average: <span className="text-[#f5c518] font-semibold">{summary.average_score.toFixed(1)}</span>
          {' '}·{' '}{fmt(summary.votes)} {summary.votes === 1 ? 'vote' : 'votes'}
        </p>
      )}
      <div className="flex items-center gap-1">
        {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
          <button key={n}
            onMouseEnter={() => setHover(n)}
            onMouseLeave={() => setHover(null)}
            onClick={() => handleRate(n)}
            className={`w-8 h-8 rounded-lg text-xs font-bold transition-all duration-100
              ${n <= active
                ? 'bg-[#f5c518] text-black scale-110'
                : 'bg-[#1a1a24] text-[#55556a] border border-[#2a2a38] hover:border-[#f5c518]/50 hover:text-[#f5c518]'
              }`}>
            {n}
          </button>
        ))}
        {summary?.my_score != null && (
          <span className="ml-2 text-xs text-[#55556a]">
            Your rating: <span className="text-[#f5c518]">{summary.my_score}</span>
          </span>
        )}
      </div>
    </div>
  )
}

// ─── comment section ──────────────────────────────────────────────────────────

function CommentSection({ movieId }) {
  const { isAuthenticated, user } = useAuth()
  const [comments, setComments] = useState([])
  const [loading, setLoading]   = useState(true)
  const [replyTo, setReplyTo]   = useState(null)   // comment id being replied to

  const load = useCallback(() => {
    if (!isAuthenticated) { setLoading(false); return }
    setLoading(true)
    getComments(movieId)
      .then(({ data }) => setComments(data.items ?? []))
      .finally(() => setLoading(false))
  }, [movieId, isAuthenticated])

  useEffect(() => { load() }, [load])

  const handleDelete = async (commentId) => {
    await deleteComment(commentId)
    setComments((cs) => cs.filter((c) => c.id !== commentId))
  }

  const handlePosted = (newComment) => {
    setComments((cs) => [newComment, ...cs])
    setReplyTo(null)
  }

  if (!isAuthenticated) return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold text-[#f1f1f1]">Comments</h3>
      <AuthPrompt text="Sign in to read and post comments" />
    </div>
  )

  // Build thread: top-level + nested replies
  const top     = comments.filter((c) => !c.parent_id)
  const replies = (parentId) => comments.filter((c) => c.parent_id === parentId)

  return (
    <div className="space-y-4">
      <h3 className="text-base font-semibold text-[#f1f1f1]">
        Comments <span className="text-[#55556a] font-normal text-sm">({comments.length})</span>
      </h3>

      {/* New top-level comment form */}
      <CommentForm
        movieId={movieId} parentId={null}
        onPosted={handlePosted}
        placeholder="Share your thoughts…"
      />

      {loading && <Spinner className="py-8" />}

      {/* Threads */}
      <div className="space-y-3">
        {top.map((comment) => (
          <div key={comment.id} className="space-y-2">
            <CommentItem
              comment={comment} userId={user?.id}
              onDelete={handleDelete}
              onReply={() => setReplyTo(replyTo === comment.id ? null : comment.id)}
              isReplying={replyTo === comment.id}
            />

            {/* Replies */}
            <div className="ml-6 border-l-2 border-[#2a2a38] pl-4 space-y-2">
              {replies(comment.id).map((r) => (
                <CommentItem key={r.id} comment={r} userId={user?.id}
                  onDelete={handleDelete}
                  onReply={null}
                />
              ))}

              {replyTo === comment.id && (
                <CommentForm
                  movieId={movieId} parentId={comment.id}
                  onPosted={handlePosted}
                  onCancel={() => setReplyTo(null)}
                  placeholder={`Replying to comment…`}
                  autoFocus
                />
              )}
            </div>
          </div>
        ))}
      </div>

      {!loading && comments.length === 0 && (
        <p className="text-sm text-[#55556a] py-4 text-center">
          No comments yet. Be the first!
        </p>
      )}
    </div>
  )
}

function CommentItem({ comment, userId, onDelete, onReply, isReplying }) {
  const isOwn = userId && comment.user_id === userId
  const [deleting, setDeleting] = useState(false)

  const handleDelete = async () => {
    if (!window.confirm('Delete this comment?')) return
    setDeleting(true)
    try { await onDelete(comment.id) }
    finally { setDeleting(false) }
  }

  return (
    <div className={`rounded-xl border p-3 transition-colors
      ${isOwn ? 'border-[#2a2a38] bg-[#16161f]' : 'border-[#1e1e28] bg-[#13131a]'}`}>
      <div className="flex items-start justify-between gap-2">
        {/* Avatar + meta */}
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-7 h-7 rounded-full bg-red-900/60 text-red-300 text-[10px]
            font-bold flex items-center justify-center shrink-0">
            {String(comment.user_id).slice(-2)}
          </div>
          <div className="flex items-center gap-1.5 min-w-0">
            <span className="text-xs font-medium text-[#9999aa] truncate">
              User #{comment.user_id}
              {isOwn && <span className="ml-1 text-[10px] text-red-500">(you)</span>}
            </span>
            <span className="text-[10px] text-[#55556a] shrink-0">
              · {relativeTime(comment.created_at)}
            </span>
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-1 shrink-0">
          {onReply && (
            <button onClick={onReply}
              className={`text-[11px] px-2 py-0.5 rounded transition-colors
                ${isReplying
                  ? 'text-red-400 bg-red-900/20'
                  : 'text-[#55556a] hover:text-[#9999aa]'}`}>
              Reply
            </button>
          )}
          {isOwn && (
            <button onClick={handleDelete} disabled={deleting}
              className="text-[11px] px-2 py-0.5 rounded text-[#55556a]
                hover:text-red-400 transition-colors">
              {deleting ? '…' : 'Delete'}
            </button>
          )}
        </div>
      </div>

      <p className="mt-2 text-sm text-[#d1d1d8] leading-relaxed whitespace-pre-wrap break-words">
        {comment.text}
      </p>
    </div>
  )
}

function CommentForm({ movieId, parentId, onPosted, onCancel, placeholder, autoFocus }) {
  const [text, setText]     = useState('')
  const [sending, setSending] = useState(false)
  const [error, setError]   = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setSending(true)
    setError(null)
    try {
      const { data } = await createComment(movieId, text.trim(), parentId)
      setText('')
      onPosted(data)
    } catch {
      setError('Failed to post comment.')
    } finally {
      setSending(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-2">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={placeholder}
        rows={parentId ? 2 : 3}
        autoFocus={autoFocus}
        maxLength={5000}
        className="w-full bg-[#1a1a24] border border-[#2a2a38] rounded-xl px-3 py-2.5
          text-sm text-[#f1f1f1] placeholder-[#55556a] resize-none
          focus:outline-none focus:border-red-600 transition-colors"
      />
      {error && <p className="text-xs text-red-400">{error}</p>}
      <div className="flex items-center gap-2">
        <button type="submit" disabled={sending || !text.trim()}
          className="px-4 py-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-40
            disabled:cursor-not-allowed text-white text-xs font-medium rounded-lg transition-colors">
          {sending ? 'Posting…' : parentId ? 'Post reply' : 'Post comment'}
        </button>
        {onCancel && (
          <button type="button" onClick={onCancel}
            className="px-3 py-1.5 text-xs text-[#55556a] hover:text-[#9999aa] transition-colors">
            Cancel
          </button>
        )}
        <span className="ml-auto text-[10px] text-[#55556a]">{text.length}/5000</span>
      </div>
    </form>
  )
}

// ─── small auth prompt ────────────────────────────────────────────────────────

function AuthPrompt({ text }) {
  return (
    <p className="text-sm text-[#55556a]">
      {text} —{' '}
      <Link to="/login" className="text-red-500 hover:text-red-400 transition-colors">Sign in</Link>
    </p>
  )
}

// ─── pill badge ───────────────────────────────────────────────────────────────

function Pill({ children }) {
  return (
    <span className="px-2 py-0.5 rounded-md bg-[#1a1a24] border border-[#2a2a38]
      text-xs text-[#9999aa]">
      {children}
    </span>
  )
}

// ─── main page ────────────────────────────────────────────────────────────────

export default function MovieDetail() {
  const { id } = useParams()
  const [movie, setMovie]   = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]   = useState(null)

  useEffect(() => {
    setLoading(true)
    getMovie(id)
      .then(({ data }) => setMovie(data))
      .catch((err) => {
        setError(err?.response?.status === 404 ? 'Movie not found.' : 'Failed to load movie.')
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <Spinner className="min-h-[60vh]" />

  if (error) return (
    <div className="max-w-2xl mx-auto px-4 py-24 text-center">
      <p className="text-[#9999aa] text-lg">{error}</p>
      <Link to="/" className="mt-4 inline-block text-sm text-red-500 hover:text-red-400">
        ← Back to movies
      </Link>
    </div>
  )

  if (!movie) return null

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 space-y-10">

      {/* Back */}
      <Link to="/"
        className="inline-flex items-center gap-1.5 text-sm text-[#9999aa] hover:text-white transition-colors">
        <svg viewBox="0 0 20 20" fill="currentColor" className="w-4 h-4">
          <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293
            3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z"
            clipRule="evenodd" />
        </svg>
        Back to movies
      </Link>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row gap-8">

        {/* Poster */}
        <div className="shrink-0 w-full sm:w-52 md:w-64">
          <div className="aspect-[2/3] rounded-2xl overflow-hidden border border-[#2a2a38]"
            style={posterStyle(movie.id)}>
            {/* Cert badge */}
            {movie.certification && (
              <div className="p-3">
                <span className="px-2 py-0.5 text-xs font-bold bg-black/50 text-[#9999aa]
                  rounded border border-[#2a2a38]">
                  {movie.certification.name}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="flex-1 space-y-4">
          <div>
            <h1 className="text-3xl font-bold text-[#f1f1f1] leading-tight">{movie.name}</h1>
            <div className="flex flex-wrap items-center gap-2 mt-2 text-sm text-[#55556a]">
              <span>{movie.year}</span>
              {movie.time && <><span>·</span><span>{timeStr(movie.time)}</span></>}
              {movie.imdb && (
                <>
                  <span>·</span>
                  <span className="flex items-center gap-1 text-[#f5c518] font-semibold">
                    <svg viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5">
                      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0
                        00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0
                        00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54
                        1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1
                        1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1
                        1 0 00.951-.69l1.07-3.292z" />
                    </svg>
                    {movie.imdb.toFixed(1)} IMDb
                  </span>
                  <span className="text-[#55556a]">({fmt(movie.votes)} votes)</span>
                </>
              )}
              {movie.meta_score != null && (
                <>
                  <span>·</span>
                  <span className="font-semibold text-green-400">
                    Metascore {movie.meta_score}
                  </span>
                </>
              )}
            </div>
          </div>

          {/* Genres */}
          {movie.genres?.length > 0 && (
            <div className="flex flex-wrap gap-1.5">
              {movie.genres.map((g) => (
                <Pill key={g.id}>{g.name}</Pill>
              ))}
            </div>
          )}

          {/* Description */}
          {movie.description && (
            <p className="text-sm text-[#9999aa] leading-relaxed max-w-prose">
              {movie.description}
            </p>
          )}

          {/* Directors / Stars */}
          <div className="space-y-1.5 text-sm">
            {movie.directors?.length > 0 && (
              <div className="flex flex-wrap gap-x-1 gap-y-0.5">
                <span className="text-[#55556a] shrink-0">Director{movie.directors.length > 1 ? 's' : ''}:</span>
                {movie.directors.map((d, i) => (
                  <span key={d.id} className="text-[#f1f1f1]">
                    {d.name}{i < movie.directors.length - 1 ? ',' : ''}
                  </span>
                ))}
              </div>
            )}
            {movie.stars?.length > 0 && (
              <div className="flex flex-wrap gap-x-1 gap-y-0.5">
                <span className="text-[#55556a] shrink-0">Stars:</span>
                {movie.stars.slice(0, 5).map((s, i) => (
                  <span key={s.id} className="text-[#f1f1f1]">
                    {s.name}{i < Math.min(movie.stars.length, 5) - 1 ? ',' : ''}
                  </span>
                ))}
                {movie.stars.length > 5 && (
                  <span className="text-[#55556a]">+{movie.stars.length - 5} more</span>
                )}
              </div>
            )}
          </div>

          {/* Price + cart */}
          <div className="flex flex-wrap items-center gap-4 pt-2">
            <span className="text-3xl font-bold text-red-500">
              ${Number(movie.price).toFixed(2)}
            </span>
            <AddToCartButton movieId={movie.id} />
          </div>
        </div>
      </div>

      {/* ── Interactions ──────────────────────────────────────────────────── */}
      <div className="border-t border-[#2a2a38] pt-8 grid sm:grid-cols-2 gap-8">

        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-[#f1f1f1] uppercase tracking-widest">
            Reactions
          </h3>
          <ReactionsBar movieId={movie.id} />
        </div>

        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-[#f1f1f1] uppercase tracking-widest">
            Rate this movie
          </h3>
          <RatingWidget movieId={movie.id} />
        </div>
      </div>

      {/* ── Comments ──────────────────────────────────────────────────────── */}
      <div className="border-t border-[#2a2a38] pt-8">
        <CommentSection movieId={movie.id} />
      </div>

    </div>
  )
}
