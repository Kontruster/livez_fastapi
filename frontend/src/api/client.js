// Единая точка входа для всех запросов к FastAPI.
// Здесь обработка JSON, ошибок и cookie-based авторизации.

const JSON_HEADERS = { 'Content-Type': 'application/json' }

// Вызывается, когда сервер ответил 401 — например, истёк токен.
// AuthContext подписывается на это, чтобы разлогинить пользователя.
let onUnauthorized = null
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

async function request(path, { method = 'GET', body, isForm = false } = {}) {
  const options = {
    method,
    credentials: 'include',
    headers: isForm ? undefined : JSON_HEADERS,
  }

  if (body !== undefined) {
    options.body = isForm ? body : JSON.stringify(body)
  }

  let res
  try {
    res = await fetch(path, options)
  } catch {
    // сеть недоступна: fetch бросает TypeError
    const error = new Error('Нет связи с сервером. Проверьте подключение.')
    error.status = 0
    throw error
  }

  if (res.status === 204) return null

  const text = await res.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = { detail: text }
    }
  }

  if (!res.ok) {
    const message =
      typeof data?.detail === 'string'
        ? data.detail
        : Array.isArray(data?.detail)
          ? data.detail
              .map((d) => (typeof d === 'string' ? d : d.msg || JSON.stringify(d)))
              .join(', ')
          : `Ошибка ${res.status}`

    const error = new Error(message)
    error.status = res.status
    error.data = data
    if (res.status === 401 && onUnauthorized) onUnauthorized()
    throw error
  }

  return data
}

// ---------- Auth (fastapi-users) ----------
export const authApi = {
  login: (email, password) => {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    // fastapi-users отвечает 204 и ставит cookie
    return request('/auth/jwt/login', { method: 'POST', body: form, isForm: true })
  },
  register: (payload) => request('/auth/register', { method: 'POST', body: payload }),
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

  // POST /posts/  — тело { text, group_id?, images? }
  create: (payload) => request('/posts/', { method: 'POST', body: payload }),

  // PATCH /posts/{id}/  — тело PostUpdate (все поля опциональны)
  update: (id, payload) => request(`/posts/${id}/`, { method: 'PATCH', body: payload }),

  // DELETE /posts/{id} — 204
  remove: (id) => request(`/posts/${id}`, { method: 'DELETE' }),

  // POST /posts/{id}/like/  -> { liked, likes_count }
  like: (id) => request(`/posts/${id}/like/`, { method: 'POST' }),

  // DELETE /posts/{id}/like/ -> { liked, likes_count }
  unlike: (id) => request(`/posts/${id}/like/`, { method: 'DELETE' }),

  // POST /posts/{id}/comments/  — тело { text, parent_id? }
  addComment: (id, text, parentId = null) =>
    request(`/posts/${id}/comments/`, {
      method: 'POST',
      body: parentId ? { text, parent_id: parentId } : { text },
    }),

  // DELETE /comments/{id} — 204
  removeComment: (id) => request(`/comments/${id}`, { method: 'DELETE' }),
}

// ---------- Groups ----------
export const groupsApi = {
  list: () => request('/groups/'),
  get: (slug) => request(`/groups/${encodeURIComponent(slug)}/`),
  create: (payload) => request('/groups/', { method: 'POST', body: payload }),

  // Членство в группе (нужно для приватных групп)
  join: (slug) =>
    request(`/groups/${encodeURIComponent(slug)}/join/`, { method: 'POST' }),
  leave: (slug) =>
    request(`/groups/${encodeURIComponent(slug)}/leave/`, { method: 'DELETE' }),
}

// ---------- Profile / Follow ----------
export const profileApi = {
  me: ({ page = 1, size = 10 } = {}) =>
    request(`/profile/me?${new URLSearchParams({ page, size })}`),
  byUsername: (username, { page = 1, size = 10 } = {}) =>
    request(
      `/profile/${encodeURIComponent(username)}?${new URLSearchParams({ page, size })}`,
    ),

  follow: (username) =>
    request(`/profile/${encodeURIComponent(username)}/follow/`, { method: 'POST' }),
  unfollow: (username) =>
    request(`/profile/${encodeURIComponent(username)}/follow/`, { method: 'DELETE' }),
}

export const accountApi = {
  changeUsername: (username) =>
    request('/users/me/profile', { method: 'PATCH', body: { username } }),

  changePassword: (oldPassword, newPassword) =>
    request('/users/me/password', {
      method: 'POST',
      body: { old_password: oldPassword, new_password: newPassword },
    }),

  uploadAvatar: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('/users/me/avatar', { method: 'POST', body: fd, isForm: true })
  },

  deleteAccount: (password) =>
    request('/users/me', { method: 'DELETE', body: { password } }),
}

export const uploadsApi = {
  postImage: (file) => {
    const fd = new FormData()
    fd.append('file', file)
    return request('/media/post-image', {
      method: 'POST',
      body: fd,
      isForm: true,
    })
  },
}

export const serviceApi = {
  health: () => request('/health'),
}
