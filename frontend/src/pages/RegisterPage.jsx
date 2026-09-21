import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()

  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const onChange = (e) => setForm({ ...form, [e.target.name]: e.target.value })

  const onSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setBusy(true)
    try {
      await register(form)
      navigate('/login', { replace: true })
    } catch (err) {
      setError(err.message || 'Не удалось зарегистрироваться')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={onSubmit}>
        <h1>Регистрация</h1>
        <label>
          Email
          <input name="email" type="email" value={form.email} onChange={onChange} required />
        </label>
        <label>
          Username
          <input name="username" value={form.username} onChange={onChange} required />
        </label>
        <label>
          Пароль
          <input
            name="password"
            type="password"
            value={form.password}
            onChange={onChange}
            required
            minLength={6}
          />
        </label>

        {error && <p className="form-error">{error}</p>}

        <button type="submit" disabled={busy}>
          {busy ? 'Создаём…' : 'Создать аккаунт'}
        </button>

        <p className="auth-hint">
          Уже есть аккаунт? <Link to="/login">Войти</Link>
        </p>
      </form>
    </div>
  )
}