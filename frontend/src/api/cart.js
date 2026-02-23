import client from './client'

// ─── localStorage cart items ──────────────────────────────────────────────────
// GET /cart/{cart_id} requires a cart_id that the API never returns.
// Instead we store the display data locally when adding items.
// Shape stored: { id, name, price, year, genres }

const ITEMS_KEY = 'cart_items'

export function getLocalCartItems() {
  try { return JSON.parse(localStorage.getItem(ITEMS_KEY)) ?? [] }
  catch { return [] }
}

export function addLocalCartItem(movie) {
  const items = getLocalCartItems()
  if (items.find((m) => m.id === movie.id)) return   // already present
  const entry = {
    id:     movie.id,
    name:   movie.name,
    price:  movie.price,
    year:   movie.year,
    genres: movie.genres ?? [],
  }
  localStorage.setItem(ITEMS_KEY, JSON.stringify([...items, entry]))
}

export function removeLocalCartItem(movieId) {
  const items = getLocalCartItems().filter((m) => m.id !== movieId)
  localStorage.setItem(ITEMS_KEY, JSON.stringify(items))
}

export function clearLocalCartItems() {
  localStorage.removeItem(ITEMS_KEY)
}

export function localCartCount() {
  return getLocalCartItems().length
}

// ─── API endpoints ────────────────────────────────────────────────────────────

export const addToCart = (movie_id) =>
  client.post('/cart/movies/', { movie_id })

export const removeFromCart = (movie_id) =>
  client.delete(`/cart/movies/${movie_id}`)

export const clearCart = () =>
  client.delete('/cart/movies/')
