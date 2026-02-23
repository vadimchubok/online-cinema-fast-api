import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import {
  getProfile, createProfile, updateProfile, uploadAvatar, changePassword,
} from '../api/auth'
import Spinner from '../components/ui/Spinner'

// ─── helpers ─────────────────────────────────────────────────────────────────

function Badge({ children, color = 'zinc' }) {
  const cls = {
    red:  'bg-red-900/30 text-red-400 border-red-800/40',
    gold: 'bg-yellow-900/30 text-yellow-400 border-yellow-800/40',
    zinc: 'bg-zinc-800 text-zinc-400 border-zinc-700',
  }[color]
  return (
    <span className={`px-2 py-0.5 rounded-md border text-[11px] font-semibold uppercase tracking-wider ${cls}`}>
      {children}
    </span>
  )
}

function roleColor(group) {
  if (group === 'ADMIN')     return 'red'
  if (group === 'MODERATOR') return 'gold'
  return 'zinc'
}

function SectionCard({ title, children }) {
  return (
    <div className="bg-[#16161f] border border-[#2a2a38] rounded-2xl overflow-hidden">
      {title && (
        <div className="px-6 py-4 border-b border-[#2a2a38]">
          <h2 className="text-sm font-semibold text-[#f1f1f1] uppercase tracking-wider">{title}</h2>
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}

function Field({ label, children }) {
  return (
    <div className="space-y-1.5">
      <label className="block text-xs font-medium text-[#9999aa] uppercase tracking-wider">
        {label}
      </label>
      {children}
    </div>
  )
}

const inputCls = `w-full bg-[#1a1a24] border border-[#2a2a38] rounded-xl px-4 py-2.5
  text-sm text-[#f1f1f1] placeholder-[#55556a]
  focus:outline-none focus:border-red-600 transition-colors`

// ─── avatar section ───────────────────────────────────────────────────────────

function AvatarSection({ profile, user, onAvatarUpdated }) {
  const fileRef  = useRef(null)
  const [preview, setPreview] = useState(null)
  const [file, setFile]       = useState(null)
  const [uploading, setUploading] = useState(false)
  const [error, setError]     = useState(null)
  const [success, setSuccess] = useState(false)

  const handleFileChange = (e) => {
    const f = e.target.files[0]
    if (!f) return
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setError(null)
    setSuccess(false)
  }

  const handleUpload = async () => {
    if (!file) return
    setUploading(true)
    setError(null)
    try {
      const { data } = await uploadAvatar(file)
      onAvatarUpdated(data.avatar_url)
      setSuccess(true)
      setFile(null)
      setTimeout(() => setSuccess(false), 3000)
    } catch {
      setError('Upload failed. Ensure the file is a valid image (JPEG/PNG).')
    } finally {
      setUploading(false)
    }
  }

  const src = preview || profile?.avatar_url
  const initials = user?.email?.slice(0, 2).toUpperCase() ?? '?'

  return (
    <div className="flex flex-col sm:flex-row items-start sm:items-center gap-5">
      {/* Avatar circle */}
      <div className="relative group shrink-0">
        {src ? (
          <img src={src} alt="avatar"
            className="w-20 h-20 rounded-full object-cover border-2 border-[#2a2a38]" />
        ) : (
          <div className="w-20 h-20 rounded-full bg-red-900/60 border-2 border-[#2a2a38]
            flex items-center justify-center text-2xl font-bold text-red-200">
            {initials}
          </div>
        )}
        <button
          onClick={() => fileRef.current?.click()}
          className="absolute inset-0 rounded-full bg-black/50 opacity-0 group-hover:opacity-100
            transition-opacity flex items-center justify-center"
          title="Change avatar"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
            className="w-5 h-5 text-white">
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0
                0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0
                0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0
                01-2-2V9z" />
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </button>
        <input ref={fileRef} type="file" accept="image/*" className="hidden"
          onChange={handleFileChange} />
      </div>

      <div className="space-y-2 min-w-0">
        <div>
          <p className="font-semibold text-[#f1f1f1]">
            {profile?.first_name && profile?.last_name
              ? `${profile.first_name} ${profile.last_name}`
              : user?.email}
          </p>
          <p className="text-sm text-[#55556a]">{user?.email}</p>
        </div>
        <Badge color={roleColor(user?.user_group)}>{user?.user_group ?? 'USER'}</Badge>

        {/* Upload controls */}
        {file && (
          <div className="flex items-center gap-2 pt-1">
            <button onClick={handleUpload} disabled={uploading}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-500 disabled:opacity-60
                text-white text-xs font-medium rounded-lg transition-colors">
              {uploading ? 'Uploading…' : 'Upload photo'}
            </button>
            <button onClick={() => { setFile(null); setPreview(null) }}
              className="text-xs text-[#55556a] hover:text-[#9999aa] transition-colors">
              Cancel
            </button>
          </div>
        )}
        {success && <p className="text-xs text-green-500">Avatar updated!</p>}
        {error   && <p className="text-xs text-red-400">{error}</p>}
        {!file   && (
          <button onClick={() => fileRef.current?.click()}
            className="text-xs text-[#55556a] hover:text-red-400 transition-colors">
            Change photo
          </button>
        )}
      </div>
    </div>
  )
}

// ─── profile form ─────────────────────────────────────────────────────────────

function ProfileForm({ profile, profileExists, onSaved }) {
  const [form, setForm] = useState({
    first_name:    profile?.first_name    ?? '',
    last_name:     profile?.last_name     ?? '',
    date_of_birth: profile?.date_of_birth ?? '',
    info:          profile?.info          ?? '',
  })
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState(null)
  const [saved,  setSaved]  = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setSaving(true)
    setError(null)
    setSaved(false)

    const payload = {
      first_name:    form.first_name    || null,
      last_name:     form.last_name     || null,
      date_of_birth: form.date_of_birth || null,
      info:          form.info          || null,
    }

    try {
      const fn = profileExists ? updateProfile : createProfile
      const { data } = await fn(payload)
      onSaved(data)
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to save profile.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Field label="First name">
          <input type="text" value={form.first_name} onChange={set('first_name')}
            placeholder="Jane" className={inputCls} />
        </Field>
        <Field label="Last name">
          <input type="text" value={form.last_name} onChange={set('last_name')}
            placeholder="Doe" className={inputCls} />
        </Field>
      </div>
      <Field label="Date of birth">
        <input type="date" value={form.date_of_birth} onChange={set('date_of_birth')}
          className={inputCls} />
      </Field>
      <Field label="Bio">
        <textarea value={form.info} onChange={set('info')}
          placeholder="Tell us a little about yourself…"
          rows={3}
          className={`${inputCls} resize-none`} />
      </Field>

      {error && (
        <p className="text-sm text-red-400 bg-red-950/30 border border-red-800/30 rounded-xl px-4 py-2">
          {error}
        </p>
      )}

      <div className="flex items-center gap-3">
        <button type="submit" disabled={saving}
          className="px-5 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-60
            text-white text-sm font-medium rounded-xl transition-colors">
          {saving ? 'Saving…' : profileExists ? 'Save changes' : 'Create profile'}
        </button>
        {saved && <span className="text-sm text-green-500">Saved!</span>}
      </div>
    </form>
  )
}

// ─── change password ──────────────────────────────────────────────────────────

function ChangePasswordForm() {
  const [form, setForm] = useState({ current_password: '', new_password: '', confirm: '' })
  const [showPw, setShowPw] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error,  setError]  = useState(null)
  const [success, setSuccess] = useState(false)

  const set = (key) => (e) => setForm((f) => ({ ...f, [key]: e.target.value }))

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (form.new_password !== form.confirm) { setError('New passwords don\'t match.'); return }
    setSaving(true)
    setError(null)
    try {
      await changePassword(form.current_password, form.new_password)
      setSuccess(true)
      setForm({ current_password: '', new_password: '', confirm: '' })
      setTimeout(() => setSuccess(false), 4000)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Failed to update password.')
    } finally {
      setSaving(false)
    }
  }

  const eyeBtn = (
    <button type="button" onClick={() => setShowPw((v) => !v)}
      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#55556a] hover:text-[#9999aa] transition-colors">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="w-4 h-4">
        {showPw
          ? <><path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" /><path strokeLinecap="round" strokeLinejoin="round" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" /></>
          : <path strokeLinecap="round" strokeLinejoin="round" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
        }
      </svg>
    </button>
  )

  return (
    <form onSubmit={handleSubmit} className="space-y-4 max-w-sm">
      <Field label="Current password">
        <div className="relative">
          <input type={showPw ? 'text' : 'password'} required value={form.current_password}
            onChange={set('current_password')} placeholder="••••••••"
            autoComplete="current-password"
            className={`${inputCls} pr-10`} />
          {eyeBtn}
        </div>
      </Field>
      <Field label="New password">
        <div className="relative">
          <input type={showPw ? 'text' : 'password'} required value={form.new_password}
            onChange={set('new_password')} placeholder="••••••••"
            autoComplete="new-password"
            className={`${inputCls} pr-10`} />
          {eyeBtn}
        </div>
      </Field>
      <Field label="Confirm new password">
        <input type={showPw ? 'text' : 'password'} required value={form.confirm}
          onChange={set('confirm')} placeholder="••••••••"
          autoComplete="new-password"
          className={`${inputCls} ${form.confirm && form.confirm !== form.new_password ? 'border-red-700' : ''}`} />
        {form.confirm && form.confirm !== form.new_password && (
          <p className="text-[11px] text-red-400 mt-1">Passwords don't match.</p>
        )}
      </Field>

      {error   && <p className="text-sm text-red-400 bg-red-950/30 border border-red-800/30 rounded-xl px-4 py-2">{error}</p>}
      {success && <p className="text-sm text-green-500">Password updated successfully!</p>}

      <button type="submit" disabled={saving}
        className="px-5 py-2 bg-red-600 hover:bg-red-500 disabled:opacity-60
          text-white text-sm font-medium rounded-xl transition-colors">
        {saving ? 'Updating…' : 'Update password'}
      </button>
    </form>
  )
}

// ─── main page ────────────────────────────────────────────────────────────────

export default function Profile() {
  const { user } = useAuth()
  const [profile, setProfile]             = useState(null)
  const [profileExists, setProfileExists] = useState(false)
  const [loading, setLoading]             = useState(true)

  useEffect(() => {
    getProfile()
      .then(({ data, status }) => {
        if (status === 204 || !data) {
          setProfileExists(false)
        } else {
          setProfile(data)
          setProfileExists(true)
        }
      })
      .catch(() => {
        // 204 may come through as an error in some axios versions
        setProfileExists(false)
      })
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Spinner className="min-h-[60vh]" />

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-10 space-y-6" id="profile-top">

      <h1 className="text-2xl font-bold text-[#f1f1f1]">My Profile</h1>

      {/* Avatar + identity */}
      <SectionCard>
        <AvatarSection
          profile={profile} user={user}
          onAvatarUpdated={(url) => setProfile((p) => ({ ...p, avatar_url: url }))}
        />
      </SectionCard>

      {/* Edit profile */}
      <SectionCard title="Profile Details">
        <ProfileForm
          profile={profile}
          profileExists={profileExists}
          onSaved={(data) => { setProfile(data); setProfileExists(true) }}
        />
      </SectionCard>

      {/* Change password */}
      <SectionCard title="Security">
        <ChangePasswordForm />
      </SectionCard>

    </div>
  )
}
