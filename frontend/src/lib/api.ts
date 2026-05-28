import { Dataset, ReviewsResponse, Summary, RateLimitStatus, ChatMessage } from '@/types'

const API_BASE = '/api/v1'

function redirectToLogin() {
  if (window.location.pathname.startsWith('/login')) return
  const next = encodeURIComponent(window.location.pathname + window.location.search)
  window.location.href = `/login?expired=1&next=${next}`
}

async function apiFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const isFormData = typeof FormData !== 'undefined' && options.body instanceof FormData
  const headers: Record<string, string> = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...(options.headers as Record<string, string> || {}),
  }

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers, credentials: 'include' })

  if (res.status === 401) {
    redirectToLogin()
    throw new Error('Unauthorized')
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw Object.assign(new Error(err.message || 'Request failed'), { status: res.status, data: err })
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

// Auth
export const authApi = {
  login: async (email: string, password: string) => {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
      credentials: 'include',
    })
    if (!res.ok) {
      const err = await res.json().catch(() => ({ message: 'Login failed' }))
      throw Object.assign(new Error(err.message || 'Login failed'), { status: res.status, data: err })
    }
    return res.json() as Promise<{ expires_at: string; user: { id: string; email: string } }>
  },
  me: () => apiFetch<{ id: string; email: string }>('/auth/me'),
  logout: () => apiFetch<void>('/auth/logout', { method: 'POST' }),
}

// Datasets
export const datasetsApi = {
  list: () => apiFetch<{ datasets: Dataset[] }>('/datasets'),
  get: (id: string) => apiFetch<Dataset>(`/datasets/${id}`),
  create: (input: string) =>
    apiFetch<{ id: string; asin: string; status: string }>('/datasets', {
      method: 'POST',
      body: JSON.stringify({ input }),
    }),
  upload: (file: File): Promise<{ id: string; status: string }> => {
    const body = new FormData()
    body.append('file', file)
    return apiFetch<{ id: string; status: string }>('/datasets/upload', { method: 'POST', body })
  },
  rescrape: (id: string) =>
    apiFetch<{ status: string }>(`/datasets/${id}/rescrape`, { method: 'POST' }),
  delete: (id: string) => apiFetch<void>(`/datasets/${id}`, { method: 'DELETE' }),
}

// Reviews & Summary
export const reviewsApi = {
  list: (id: string, params: Record<string, string | number>) => {
    const qs = new URLSearchParams(Object.entries(params).map(([k, v]) => [k, String(v)])).toString()
    return apiFetch<ReviewsResponse>(`/datasets/${id}/reviews?${qs}`)
  },
  summary: (id: string) => apiFetch<Summary>(`/datasets/${id}/summary`),
}

// Rate limit
export const scrapeApi = {
  rateLimit: () => apiFetch<RateLimitStatus>('/scrape/rate-limit'),
}

// Chat
export const chatApi = {
  send: (datasetId: string, message: string, history: ChatMessage[]) =>
    apiFetch<{ reply: string; scope_refused: boolean }>(`/datasets/${datasetId}/chat`, {
      method: 'POST',
      body: JSON.stringify({
        message,
        history: history.map(h => ({ role: h.role, content: h.content })),
      }),
    }),
}
