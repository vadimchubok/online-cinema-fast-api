import client from './client'

// Cart ID is returned by the backend and stored locally so we can fetch cart contents.
// It is set the first time we successfully retrieve or create a cart.

const CART_ID_KEY = 'cart_id'

export const getStoredCartId  = ()       => localStorage.getItem(CART_ID_KEY)
export const storeCartId      = (id)     => localStorage.setItem(CART_ID_KEY, id)
export const clearStoredCartId = ()      => localStorage.removeItem(CART_ID_KEY)

// ─── endpoints ────────────────────────────────────────────────────────────────

export const addToCart = (movie_id) =>
  client.post('/cart/movies/', { movie_id })

export const removeFromCart = (movie_id) =>
  client.delete(`/cart/movies/${movie_id}`)

export const clearCart = () =>
  client.delete('/cart/movies/')

/** Pass the cart_id obtained from the user's cart resource. */
export const getCart = (cartId) =>
  client.get(`/cart/${cartId}`)
