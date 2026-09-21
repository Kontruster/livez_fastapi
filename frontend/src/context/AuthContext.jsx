import { createContext, useContext, useEffect, useState } from 'react'
import { authApi } from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  // При старте пробуем получить текущего пользователя.
  // Если cookie валидная — вернётся объект, если нет — 401 и мы просто
  // остаёмся "не залогинены".
  useEffect(() => {
    authApi
      .me()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false))
  }, [])

  const login = async (email, password) => {
    await authApi.login(email, password)
    const me = await authApi.me()
    setUser(me)
  }

  const register = async (payload) => {
    await authApi.register(payload)
    // после регистрации fastapi-users не логинит автоматически
    // (если хочешь — сделаем авто-логин, скажи)
  }

  const logout = async () => {
    await authApi.logout()
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, setUser, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>')
  return ctx
}