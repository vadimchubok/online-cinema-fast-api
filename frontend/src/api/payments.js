import client from './client'

/** Current user's payments. */
export const getMyPayments = (params = {}) =>
  client.get('/payment/my', { params })

/** Admin: all payments. */
export const getAllPayments = (params = {}) =>
  client.get('/payment/', { params })

export const refundPayment = (paymentId) =>
  client.post(`/payment/${paymentId}/refund`)
