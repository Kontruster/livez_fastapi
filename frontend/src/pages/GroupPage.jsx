import { useEffect, useState, useCallback } from 'react'
import { useParams, Link } from 'react-router-dom'
import { postsApi, groupsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import PostCard from '../components/PostCard'
import PostForm from '../components/PostForm'

const SIZE = 10

export default function GroupPage() {
  const { slug } = useParams()
  const { user } = useAuth()
  const toast = useToast()

  const [group, setGroup] = useState(null)
  const [items, setItems] = useState([])
  const [page, setPage] = useState(1)
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [forbidden, setForbidden] = useState(false)
  const [error, setError] = useState('')
  const [membershipBusy, setMembershipBusy] = useState(false)

  const load = useCallback(() => {
    let cancelled = false
    setLoading(true)
    setError('')
    setForbidden(false)

    postsApi
      .groupFeed(slug, { page, size: SIZE })
      .then((data) => {
        if (cancelled) return
        setGroup(data.group)
        setItems(data.posts?.items || [])
        setPages(data.posts?.pages || 1)
      })
      .catch((err) => {
        if (cancelled) return
        if (err.status === 403) setForbidden(true)
        else setError(err.message || 'Группа не найдена')
      })
      .finally(() => !cancelled && setLoading(false))

    return () => {
      cancelled = true
    }
  }, [slug, page])

  useEffect(load, [load])

  const onCreated = (created) => {
    if (page === 1) setItems((prev) => [created, ...prev])
    toast.success('Пост опубликован')
  }

  const onLikeChange = (postId, state) =>
    setItems((prev) => prev.map((p) => (p.id === postId ? { ...p, ...state } : p)))

  const onMembershipToggle = async () => {
    if (!group || membershipBusy) return
    setMembershipBusy(true)
    const isMember = group.is_member
    try {
      const updated = isMember
        ? await groupsApi.leave(group.slug)
        : await groupsApi.join(group.slug)

      setGroup((g) => ({ ...g, ...updated }))
      toast.success(isMember ? 'Вы вышли из группы' : 'Вы вступили в группу')

      if (!isMember) load()
    } catch (err) {
      toast.error(err.message || 'Не удалось изменить членство')
    } finally {
      setMembershipBusy(false)
    }
  }

  if (loading) {
    return (
      <div className="group-page">
        <Link to="/groups" className="profile__hint">
          ← Ко всем группам
        </Link>
        <p className="page-loading">Загружаем…</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="group-page">
        <Link to="/groups" className="profile__hint">
          ← Ко всем группам
        </Link>
        <p className="form-error">{error}</p>
      </div>
    )
  }

  // --- Закрытая группа без доступа ---
  if (forbidden) {
    return (
      <div className="group-access">
        <h1 className="page-title">Закрытая группа</h1>
        <p className="group-access__text">
          @{slug} — приватная. Посты видны только участникам.
        </p>
        <button
          type="button"
          className="btn-primary"
          onClick={onMembershipToggle}
          disabled={membershipBusy || !user}
        >
          {membershipBusy
            ? '…'
            : user
              ? 'Вступить в группу'
              : 'Войдите, чтобы вступить'}
        </button>
        <Link to="/groups" className="profile__hint">
          ← Ко всем группам
        </Link>
      </div>
    )
  }

  return (
    <div className="group-page">
      <Link to="/groups" className="profile__hint">
        ← Ко всем группам
      </Link>

      <header className="group-page__head">
        <h1 className="page-title">
          {group?.title || `@${slug}`}
          {group?.is_private && <span className="badge-private">приватная</span>}
        </h1>
        {group?.description && <p className="group-page__desc">{group.description}</p>}

        {group && (
          <div className="group-page__meta">
            <span className="group-page__stat">
              <b>{group.members_count ?? 0}</b> участников
            </span>
            {group.is_private && (
              <span className="group-page__stat group-page__stat--private">
                только для участников
              </span>
            )}
          </div>
        )}

        {user && group && (
          <button
            type="button"
            className={group.is_member ? 'btn-ghost' : 'btn-primary'}
            onClick={onMembershipToggle}
            disabled={membershipBusy}
          >
            {membershipBusy
              ? '…'
              : group.is_member
                ? 'Покинуть группу'
                : 'Вступить в группу'}
          </button>
        )}
      </header>

      {user && group && group.is_member !== false && (
        <PostForm fixedGroupId={group.id} onCreated={onCreated} />
      )}

      {loading && <p className="page-loading">Загружаем…</p>}
      {error && <p className="form-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="feed__empty">В этой группе пока нет постов</p>
      )}

      <div className="feed__list">
        {items.map((post) => (
          <PostCard key={post.id} post={post} onLikeChange={onLikeChange} />
        ))}
      </div>

      {pages > 1 && (
        <div className="pagination">
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
          >
            ← Назад
          </button>
          <span className="pagination__info">
            {page} из {pages}
          </span>
          <button
            type="button"
            className="btn-ghost"
            onClick={() => setPage((p) => Math.min(pages, p + 1))}
            disabled={page >= pages}
          >
            Вперёд →
          </button>
        </div>
      )}
    </div>
  )
}
