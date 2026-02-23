import { useState, useEffect } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import {
  getGenres, createGenre,
  getStars, createStar,
  createMovie,
} from '../api/movies'

// ─── shared styles ────────────────────────────────────────────────────────────

const inputCls = `w-full bg-[#1a1a24] border border-[#2a2a38] rounded-xl px-4 py-2.5
  text-sm text-[#f1f1f1] placeholder-[#55556a]
  focus:outline-none focus:border-red-600 transition-colors`

function Field({ label, required, children }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-[#9999aa] uppercase tracking-wider">
        {label}{required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
    </div>
  )
}

function SaveBtn({ saving, label = 'Create', savingLabel = 'Creating…' }) {
  return (
    <button type="submit" disabled={saving}
      className="px-5 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-60
        text-white text-sm font-medium rounded-xl transition-colors">
      {saving ? savingLabel : label}
    </button>
  )
}

function Alert({ type, msg }) {
  if (!msg) return null
  const cls = type === 'error'
    ? 'bg-red-950/40 border-red-800/40 text-red-400'
    : 'bg-green-950/40 border-green-700/40 text-green-400'
  return (
    <div className={`border rounded-xl px-4 py-2.5 text-sm ${cls}`}>{msg}</div>
  )
}

// ─── certification constants (seeded, no API endpoint) ────────────────────────

const CERTIFICATIONS = [
  { id: 1, name: 'G' },
  { id: 2, name: 'PG' },
  { id: 3, name: 'PG-13' },
  { id: 4, name: 'R' },
  { id: 5, name: 'NC-17' },
]

// ─── multi-select chips ───────────────────────────────────────────────────────

function ChipSelect({ items, selected, onToggle, labelKey = 'name' }) {
  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => {
        const active = selected.includes(item.id)
        return (
          <button
            key={item.id}
            type="button"
            onClick={() => onToggle(item.id)}
            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors
              ${active
                ? 'bg-red-600 text-white'
                : 'bg-[#1a1a24] text-[#9999aa] border border-[#2a2a38] hover:border-red-600/50'
              }`}
          >
            {item[labelKey]}
          </button>
        )
      })}
    </div>
  )
}

// ─── genre tab ────────────────────────────────────────────────────────────────

function GenreTab() {
  const [genres,  setGenres]  = useState([])
  const [name,    setName]    = useState('')
  const [saving,  setSaving]  = useState(false)
  const [msg,     setMsg]     = useState(null) // { type, text }

  const load = () => getGenres().then(({ data }) => setGenres(data)).catch(() => {})

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    setMsg(null)
    try {
      await createGenre({ name: name.trim() })
      setMsg({ type: 'ok', text: `Genre "${name.trim()}" created.` })
      setName('')
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err?.response?.data?.detail || 'Failed to create genre.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
        <Field label="Genre name" required>
          <input
            type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Thriller" className={inputCls} required
          />
        </Field>
        <Alert type={msg?.type} msg={msg?.text} />
        <SaveBtn saving={saving} />
      </form>

      {genres.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[#9999aa] uppercase tracking-wider mb-3">
            Existing genres
          </p>
          <div className="flex flex-wrap gap-2">
            {genres.map((g) => (
              <span key={g.id}
                className="px-3 py-1 rounded-full text-xs bg-[#1a1a24] text-[#9999aa]
                  border border-[#2a2a38]">
                {g.name}
                <span className="ml-1.5 text-[#55556a]">{g.movie_count}</span>
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── star tab ─────────────────────────────────────────────────────────────────

function StarTab() {
  const [stars,   setStars]   = useState([])
  const [name,    setName]    = useState('')
  const [saving,  setSaving]  = useState(false)
  const [msg,     setMsg]     = useState(null)

  const load = () => getStars({ limit: 200 }).then(({ data }) => setStars(data)).catch(() => {})

  useEffect(() => { load() }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim()) return
    setSaving(true)
    setMsg(null)
    try {
      await createStar({ name: name.trim() })
      setMsg({ type: 'ok', text: `Star "${name.trim()}" created.` })
      setName('')
      load()
    } catch (err) {
      setMsg({ type: 'error', text: err?.response?.data?.detail || 'Failed to create star.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-6">
      <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
        <Field label="Actor / Star name" required>
          <input
            type="text" value={name} onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Cillian Murphy" className={inputCls} required
          />
        </Field>
        <Alert type={msg?.type} msg={msg?.text} />
        <SaveBtn saving={saving} />
      </form>

      {stars.length > 0 && (
        <div>
          <p className="text-xs font-medium text-[#9999aa] uppercase tracking-wider mb-3">
            Existing stars ({stars.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {stars.map((s) => (
              <span key={s.id}
                className="px-3 py-1 rounded-full text-xs bg-[#1a1a24] text-[#9999aa]
                  border border-[#2a2a38]">
                {s.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

// ─── movie tab ────────────────────────────────────────────────────────────────

const EMPTY_MOVIE = {
  name: '', year: new Date().getFullYear(), time: '', imdb: '',
  votes: '', meta_score: '', gross: '', description: '',
  price: '', certification_id: 4, // default R
  genre_ids: [], star_ids: [],
}

function MovieTab() {
  const [form,    setForm]    = useState(EMPTY_MOVIE)
  const [genres,  setGenres]  = useState([])
  const [stars,   setStars]   = useState([])
  const [saving,  setSaving]  = useState(false)
  const [msg,     setMsg]     = useState(null)

  useEffect(() => {
    getGenres().then(({ data }) => setGenres(data)).catch(() => {})
    getStars({ limit: 200 }).then(({ data }) => setStars(data)).catch(() => {})
  }, [])

  const set = (key) => (e) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  const toggleId = (key, id) =>
    setForm((f) => ({
      ...f,
      [key]: f[key].includes(id) ? f[key].filter((x) => x !== id) : [...f[key], id],
    }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setMsg(null)
    try {
      const payload = {
        name:           form.name.trim(),
        year:           Number(form.year),
        time:           Number(form.time),
        imdb:           Number(form.imdb),
        votes:          Number(form.votes),
        meta_score:     form.meta_score ? Number(form.meta_score) : null,
        gross:          form.gross      ? Number(form.gross)      : null,
        description:    form.description.trim(),
        price:          form.price,
        certification_id: Number(form.certification_id),
        genre_ids:      form.genre_ids,
        star_ids:       form.star_ids,
        director_ids:   [],
      }
      const { data } = await createMovie(payload)
      setMsg({ type: 'ok', text: `Movie "${data.name}" created (ID: ${data.id}).` })
      setForm(EMPTY_MOVIE)
    } catch (err) {
      setMsg({ type: 'error', text: err?.response?.data?.detail || 'Failed to create movie.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5 max-w-2xl">
      {/* Basic info */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="Title" required>
          <input type="text" value={form.name} onChange={set('name')}
            placeholder="e.g. Oppenheimer" className={inputCls} required />
        </Field>
        <Field label="Year" required>
          <input type="number" value={form.year} onChange={set('year')}
            min={1888} max={2030} className={inputCls} required />
        </Field>
        <Field label="Duration (min)" required>
          <input type="number" value={form.time} onChange={set('time')}
            placeholder="e.g. 120" min={1} className={inputCls} required />
        </Field>
        <Field label="Price ($)" required>
          <input type="number" value={form.price} onChange={set('price')}
            placeholder="e.g. 4.99" step="0.01" min={0} className={inputCls} required />
        </Field>
        <Field label="IMDb score" required>
          <input type="number" value={form.imdb} onChange={set('imdb')}
            placeholder="e.g. 8.5" step="0.1" min={0} max={10} className={inputCls} required />
        </Field>
        <Field label="IMDb votes" required>
          <input type="number" value={form.votes} onChange={set('votes')}
            placeholder="e.g. 500000" min={0} className={inputCls} required />
        </Field>
        <Field label="Meta score">
          <input type="number" value={form.meta_score} onChange={set('meta_score')}
            placeholder="e.g. 88" min={0} max={100} className={inputCls} />
        </Field>
        <Field label="Box office gross ($M)">
          <input type="number" value={form.gross} onChange={set('gross')}
            placeholder="e.g. 952.3" step="0.1" min={0} className={inputCls} />
        </Field>
      </div>

      <Field label="Description" required>
        <textarea value={form.description} onChange={set('description')}
          placeholder="Brief synopsis…" rows={3}
          className={`${inputCls} resize-none`} required />
      </Field>

      {/* Certification */}
      <Field label="Certification" required>
        <div className="flex flex-wrap gap-2">
          {CERTIFICATIONS.map((c) => (
            <button key={c.id} type="button"
              onClick={() => setForm((f) => ({ ...f, certification_id: c.id }))}
              className={`px-4 py-1.5 rounded-full text-xs font-bold transition-colors
                ${form.certification_id === c.id
                  ? 'bg-red-600 text-white'
                  : 'bg-[#1a1a24] text-[#9999aa] border border-[#2a2a38] hover:border-red-600/50'
                }`}>
              {c.name}
            </button>
          ))}
        </div>
      </Field>

      {/* Genres */}
      {genres.length > 0 && (
        <Field label="Genres">
          <ChipSelect
            items={genres} selected={form.genre_ids}
            onToggle={(id) => toggleId('genre_ids', id)}
          />
        </Field>
      )}

      {/* Stars */}
      {stars.length > 0 && (
        <Field label="Stars">
          <ChipSelect
            items={stars} selected={form.star_ids}
            onToggle={(id) => toggleId('star_ids', id)}
          />
        </Field>
      )}

      <Alert type={msg?.type} msg={msg?.text} />
      <SaveBtn saving={saving} label="Create Movie" savingLabel="Creating…" />
    </form>
  )
}

// ─── tabs ─────────────────────────────────────────────────────────────────────

const TABS = [
  { id: 'genres', label: 'Genres' },
  { id: 'stars',  label: 'Stars'  },
  { id: 'movies', label: 'Movies' },
]

// ─── main page ────────────────────────────────────────────────────────────────

export default function Admin() {
  const { isModerator, loading } = useAuth()
  const [tab, setTab] = useState('genres')

  if (loading) return null
  if (!isModerator) return <Navigate to="/" replace />

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-6">
      <h1 className="text-2xl font-bold text-[#f1f1f1]">Admin Panel</h1>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-[#2a2a38] pb-px">
        {TABS.map((t) => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg transition-colors
              ${tab === t.id
                ? 'text-white border-b-2 border-red-600 -mb-px bg-[#16161f]'
                : 'text-[#9999aa] hover:text-white hover:bg-white/5'
              }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Panel */}
      <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl p-6">
        {tab === 'genres' && <GenreTab />}
        {tab === 'stars'  && <StarTab  />}
        {tab === 'movies' && <MovieTab />}
      </div>
    </div>
  )
}
