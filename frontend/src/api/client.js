// Единая точка входа для всех запросов к FastAPI.
// Здесь обработка JSON, ошибок и cookie-based авторизации.

const JSON_HEADERS = { 'Content-Type': 'application/json' }

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const options = {
    method,
    credentials: 'include', // обязательно: шлём cookie с сессией
    headers: isForm ? undefined : JSON_HEADERS,
  }

  if (body !== undefined) {
    options.body = isForm ? body : JSON.stringify(body)
  }

  const res = await fetch(path, options)

  if (res.status === 204) return null

  const text = await res.text()
  const data = text ? JSON.parse(text) : null

  if (!res.ok) {
    const message =
      typeof data?.detail === 'string'
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail.map((d) => d.msg || d).join(', ')
          : `HTTP ${res.status}`
    const error = new Error(message)
    error.status = res.status
    error.data = data
    throw error
  }

  return data
}

// ---------- Auth (fastapi-users) ----------
export const authApi = {
  // Логин — form-urlencoded, поле называется username (туда кладём email)
  login: (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    return request('/auth/jwt/login', { method: 'POST', body: form, isForm: true })
  },
  register: (payload) =>
    request('/auth/register', { method: 'POST', body: payload }),
  logout: () => request('/auth/jwt/logout', { method: 'POST' }),
  me: () => request('/users/me'),
}

// ---------- Posts ----------
export const postsApi = {
  // GET /posts/?page=&size=&q=
  feed: ({ page = 1, size = 10, q } = {}) => {
    const params = new URLSearchParams({ page, size })
    if (q) params.set('q', q)
    return request(`/posts/?${params}`)
  },

  // GET /follow/?page=&size=
  followFeed: ({ page = 1, size = 10 } = {}) => {
    const params = new URLSearchParams({ page, size })
    return request(`/follow/?${params}`)
  },

  // GET /groups/{slug}/?page=&size=
  groupFeed: (slug, { page = 1, size = 10 } = {}) => {
    const params = new URLSearchParams({ page, size })
    return request(`/groups/${encodeURIComponent(slug)}/?${params}`)
  },

  // GET /posts/{id}
  detail: (id) => request(`/posts/${id}`),

  // POST /posts/  — предполагаю тело { text, group_id?, image? }
  create: (payload) => request('/posts/', { method: 'POST', body: payload }),

  // PATCH /posts/{id}/  — тело тоже PostCreate
  update: (id, payload) =>
    request(`/posts/${id}/`, { method: 'PATCH', body: payload }),

  // DELETE /posts/{id}
  remove: (id) => request(`/posts/${id}`, { method: 'DELETE' }),

  // POST /posts/{id}/comments/  — тело { text }
  addComment: (id, text) =>
    request(`/posts/${id}/comments/`, { method: 'POST', body: { text } }),
}

// ---------- Groups ----------
export const groupsApi = {
  list: () => request('/groups/'),
}

// ---------- Profile / Follow ----------
export const profileApi = {
  me: () => request('/profile/me'),
  byUsername: (username) =>
    request(`/profile/${encodeURIComponent(username)}`),

  follow: (username) =>
    request(`/profile/${encodeURIComponent(username)}/follow/`, {
      method: 'POST',
    }),
  unfollow: (username) =>
    request(`/profile/${encodeURIComponent(username)}/follow/`, {
      method: 'DELETE',
    }),
}