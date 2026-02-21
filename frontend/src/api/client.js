import axios from 'axios'

const BASE_URL = '/api/v1'

const client = axios.create({
  baseURL: BASE_URL,
})

// ─── helpers ────────────────────────────────────────────────────────────────

function getAccessToken()  { return localStorage.getItem('access_token') }
function getRefreshToken() { return localStorage.getItem('refresh_token') }

function saveTokens({ access_token, refresh_token }) {
  localStorage.setItem('access_token',  access_token)
  localStorage.setItem('refresh_token', refresh_token)
}

function clearTokens() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('cart_id')
}

// ─── request interceptor — attach access token ───────────────────────────────

client.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ─── response interceptor — refresh on 401, retry once ───────────────────────

let isRefreshing = false
let queue = []          // queued requests waiting for a fresh token

function processQueue(error, token = null) {
  queue.forEach(({ resolve, reject }) =>
    error ? reject(error) : resolve(token)
  )
  queue = []
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config

    // Only handle 401 once per request; skip refresh endpoint itself
    if (
      error.response?.status !== 401 ||
      original._retried ||
      original.url?.includes('/user/refresh/')
    ) {
      return Promise.reject(error)
    }

    original._retried = true

    if (isRefreshing) {
      // Another refresh is in flight — queue this request
      return new Promise((resolve, reject) => {
        queue.push({ resolve, reject })
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`
        return client(original)
      })
    }

    isRefreshing = true
    const refreshToken = getRefreshToken()

    if (!refreshToken) {
      clearTokens()
      window.location.href = '/login'
      return Promise.reject(error)
    }

    try {
      const { data } = await axios.post(`${BASE_URL}/user/refresh/`, {
        refresh_token: refreshToken,
      })
      saveTokens(data)
      processQueue(null, data.access_token)
      original.headers.Authorization = `Bearer ${data.access_token}`
      return client(original)
    } catch (refreshError) {
      processQueue(refreshError, null)
      clearTokens()
      window.location.href = '/login'
      return Promise.reject(refreshError)
    } finally {
      isRefreshing = false
    }
  }
)

export { saveTokens, clearTokens, getAccessToken }
export default client
