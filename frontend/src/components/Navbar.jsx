import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  return (
    <header className="navbar">
      <Link to="/" className="brand">LiveZ</Link>

      <nav className="nav-links">
        <NavLink to="/">Лента</NavLink>
        <NavLink to="/groups">Группы</NavLink>
      </nav>

      <div className="nav-user">
        {user ? (
          <>
            <Link to="/profile/me" className="nav-username">
              {user.username || user.email}
            </Link>
            <button className="btn-ghost" onClick={onLogout}>Выйти</button>
          </>
        ) : (
          <Link to="/login">Войти</Link>
        )}
      </div>
    </header>
  )
}