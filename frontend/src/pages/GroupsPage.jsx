import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { groupsApi } from '../api/client'

export default function GroupsPage() {
  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    groupsApi
      .list()
      .then((data) => !cancelled && setGroups(data || []))
      .catch((err) => !cancelled && setError(err.message || 'Не удалось загрузить'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [])

  if (loading) return <p className="page-loading">Загружаем группы…</p>
  if (error) return <p className="form-error">{error}</p>

  return (
    <div className="groups-page">
      <h1 className="page-title">Группы</h1>

      {groups.length === 0 && (
        <p className="feed__empty">Групп пока нет</p>
      )}

      <ul className="groups-grid">
        {groups.map((g) => (
          <li key={g.id} className="group-card">
            <Link to={`/groups/${g.slug}`} className="group-card__link">
              <h2 className="group-card__title">{g.title}</h2>
              <p className="group-card__slug">@{g.slug}</p>
              {g.description && (
                <p className="group-card__desc">{g.description}</p>
              )}
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}