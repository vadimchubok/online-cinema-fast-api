import client from './client'

// ─── account ─────────────────────────────────────────────────────────────────

export const register = (email, password) =>
  client.post('/user/register/', { email, password })

export const login = (email, password) =>
  client.post('/user/login/', { email, password })

export const logout = () =>
  client.post('/user/logout/')

export const activate = (token) =>
  client.post('/user/activate/', { token })

export const getMe = () =>
  client.get('/user/me/')

export const refreshToken = (refresh_token) =>
  client.post('/user/refresh/', { refresh_token })

// ─── password ────────────────────────────────────────────────────────────────

export const requestPasswordReset = (email) =>
  client.post('/user/password-reset/request/', { email })

export const confirmPasswordReset = (token, new_password) =>
  client.post('/user/password-reset/confirm/', { token, new_password })

export const changePassword = (current_password, new_password) =>
  client.post('/user/password-change/', { current_password, new_password })

// ─── profile ─────────────────────────────────────────────────────────────────

export const createProfile = (data) =>
  client.post('/user/profile/create/', data)

export const getProfile = () =>
  client.get('/user/profile/')

export const updateProfile = (data) =>
  client.patch('/user/profile/', data)

export const uploadAvatar = (file) => {
  const form = new FormData()
  form.append('file', file)
  return client.patch('/user/profile/avatar/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
