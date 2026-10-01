import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Navbar() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const onLogout = async () => {
    await logout()
    navigate('/login', { replace: true })
  }

  const initial = (user?.username || user?.email || '?')[0].toUpperCase()

  return (
    <>
      {/* --- Desktop: вертикальный сайдбар --- */}
      <aside className="sidebar">
        <Link to="/" className="sidebar__brand">
          Live<span>Z</span>
        </Link>

        <nav className="sidebar__nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              'sidebar__link' + (isActive ? ' active' : '')
            }
          >
            <span className="sidebar__icon">🏠</span>
            Лента
          </NavLink>

          <NavLink
            to="/groups"
            className={({ isActive }) =>
              'sidebar__link' + (isActive ? ' active' : '')
            }
          >
            <span className="sidebar__icon">👥</span>
            Группы
          </NavLink>

          {user && (
            <NavLink
              to="/profile/me"
              className={({ isActive }) =>
                'sidebar__link' + (isActive ? ' active' : '')
              }
            >
              <span className="sidebar__icon">👤</span>
              Профиль
            </NavLink>
          )}
        </nav>

        <div className="sidebar__spacer" />

        {user ? (
          <div className="sidebar__user">
            <Link to="/profile/me" className="sidebar__user-main">
              {user.avatar_url ? (
                <img className="avatar-xs" src={user.avatar_url} alt="" />
              ) : (
                <span className="avatar-xs">{initial}</span>
              )}
              <span className="sidebar__username">
                {user.username || user.email}
              </span>
            </Link>
            <Link to="/settings" className="nav-icon-link" title="Настройки">
              ⚙
            </Link>
            <button
              type="button"
              className="btn-ghost btn-small"
              onClick={onLogout}
              title="Выйти"
            >
              Выйти
            </button>
          </div>
        ) : (
          <Link to="/login" className="btn-primary" style={{ textAlign: 'center' }}>
            Войти
          </Link>
        )}
      </aside>

      {/* --- Mobile: верхний навбар --- */}
      <header className="topbar">
        <Link to="/" className="topbar__brand">
          Live<span>Z</span>
        </Link>
        <nav className="topbar__nav">
          <NavLink
            to="/"
            end
            className={({ isActive }) =>
              'topbar__link' + (isActive ? ' active' : '')
            }
          >
            Лента
          </NavLink>
          <NavLink
            to="/groups"
            className={({ isActive }) =>
              'topbar__link' + (isActive ? ' active' : '')
            }
          >
            Группы
          </NavLink>
        </nav>
        <div className="topbar__user">
          {user && (
            <Link to="/profile/me">
              {user.avatar_url ? (
                <img className="avatar-xs" src={user.avatar_url} alt="" />
              ) : (
                <span className="avatar-xs">{initial}</span>
              )}
            </Link>
          )}
        </div>
      </header>
    </>
  )
}