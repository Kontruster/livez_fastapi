import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { groupsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import GroupCreateModal from '../components/GroupCreateModal'

export default function GroupsPage() {
  const { user } = useAuth()
  const toast = useToast()

  const [groups, setGroups] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [creating, setCreating] = useState(false)

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

  const onCreated = (created) => {
    setGroups((prev) => [created, ...prev])
    toast.success(`Группа «${created.title}» создана`)
  }

  return (
    <div className="groups-page">
      <header className="groups-page__head">
        <h1 className="page-title">Группы</h1>
        {user && (
          <button
            type="button"
            className="btn-primary"
            onClick={() => setCreating(true)}
          >
            + Создать группу
          </button>
        )}
      </header>

      {loading && <p className="page-loading">Загружаем группы…</p>}
      {error && <p className="form-error">{error}</p>}

      {!loading && !error && groups.length === 0 && (
        <p className="feed__empty">
          Групп пока нет — создайте первую!
        </p>
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

      <GroupCreateModal
        open={creating}
        onClose={() => setCreating(false)}
        onCreated={onCreated}
      />
    </div>
  )
}