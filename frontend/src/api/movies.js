import client from './client'

// ─── movies ───────────────────────────────────────────────────────────────────

/**
 * @param {Object} params
 * @param {number}  params.skip
 * @param {number}  params.limit
 * @param {string}  params.search
 * @param {string}  params.sort_by  — price_asc | price_desc | year_desc | popularity
 * @param {number}  params.genre_id
 */
export const getMovies = (params = {}) =>
  client.get('/movies', { params })

export const getMovie = (movieId) =>
  client.get(`/movies/${movieId}/`)

export const createMovie = (data) =>
  client.post('/movies', data)

export const updateMovie = (movieId, data) =>
  client.patch(`/movies/${movieId}/`, data)

export const deleteMovie = (movieId) =>
  client.delete(`/movies/${movieId}/`)

// ─── genres ───────────────────────────────────────────────────────────────────

export const getGenres = () =>
  client.get('/genres')

export const createGenre = (data) =>
  client.post('/genres', data)

// ─── stars ────────────────────────────────────────────────────────────────────

export const getStars = (params = {}) =>
  client.get('/stars', { params })

export const createStar = (data) =>
  client.post('/stars', data)
