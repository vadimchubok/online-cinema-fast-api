import client from './client'

/** Create a new order from the current cart. Response includes `payment_url`. */
export const createOrder = () =>
  client.post('/order/')

/** Current user's orders. */
export const getMyOrders = () =>
  client.get('/order/my')

/** Cancel a PENDING order. */
export const cancelOrder = (orderId) =>
  client.patch(`/order/${orderId}`)

// ─── admin ────────────────────────────────────────────────────────────────────

export const getAllOrders = (params = {}) =>
  client.get('/order/', { params })

export const getOrder = (orderId) =>
  client.get(`/order/${orderId}/`)
