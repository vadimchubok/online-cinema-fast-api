import client from './client'

// ─── favorites ────────────────────────────────────────────────────────────────

export const addFavorite = (movie_id) =>
  client.post('/interactions/favorites/', { movie_id })

export const removeFavorite = (movie_id) =>
  client.delete(`/interactions/favorites/${movie_id}/`)

export const getFavorites = (q = '') =>
  client.get('/interactions/favorites/', { params: q ? { q } : {} })

// ─── reactions ────────────────────────────────────────────────────────────────

/** reaction: 'LIKE' | 'DISLIKE' */
export const setReaction = (movie_id, reaction) =>
  client.post('/interactions/movies/reaction/', { movie_id, reaction })

export const removeReaction = (movie_id) =>
  client.delete(`/interactions/movies/${movie_id}/reaction/`)

export const getReactions = (movie_id) =>
  client.get(`/interactions/movies/${movie_id}/reactions/`)

// ─── ratings ──────────────────────────────────────────────────────────────────

/** score: 1–10 */
export const setRating = (movie_id, score) =>
  client.post('/interactions/movies/rating/', { movie_id, score })

export const removeRating = (movie_id) =>
  client.delete(`/interactions/movies/${movie_id}/rating/`)

export const getRating = (movie_id) =>
  client.get(`/interactions/movies/${movie_id}/rating/`)

// ─── comments ─────────────────────────────────────────────────────────────────

export const createComment = (movie_id, text, parent_id = null) =>
  client.post('/interactions/movies/comments/', { movie_id, text, ...(parent_id ? { parent_id } : {}) })

export const getComments = (movie_id, params = {}) =>
  client.get(`/interactions/movies/${movie_id}/comments/`, { params })

export const deleteComment = (comment_id) =>
  client.delete(`/interactions/comments/${comment_id}/`)

// ─── notifications ────────────────────────────────────────────────────────────

export const getNotifications = (params = {}) =>
  client.get('/interactions/notifications/', { params })

export const markNotificationRead = (notification_id) =>
  client.patch(`/interactions/notifications/${notification_id}/read/`)
