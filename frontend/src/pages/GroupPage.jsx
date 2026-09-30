import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { postsApi } from '../api/client'
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
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    postsApi
      .groupFeed(slug, { page, size: SIZE })
      .then((data) => {
        if (cancelled) return
        setGroup(data.group)
        setItems(data.posts?.items || [])
        setPages(data.posts?.pages || 1)
      })
      .catch((err) => !cancelled && setError(err.message || 'Группа не найдена'))
      .finally(() => !cancelled && setLoading(false))

    return () => {
      cancelled = true
    }
  }, [slug, page])

  const onCreated = (created) => {
    if (page === 1) setItems((prev) => [created, ...prev])
    toast.success('Пост опубликован')
  }

  return (
    <div className="group-page">
      <Link to="/groups" className="profile__hint">
        ← Ко всем группам
      </Link>

      <header className="group-page__head">
        <h1 className="page-title">{group?.title || `@${slug}`}</h1>
        {group?.description && (
          <p className="group-page__desc">{group.description}</p>
        )}
      </header>

      {user && group && (
        <PostForm fixedGroupId={group.id} onCreated={onCreated} />
      )}

      {loading && <p className="page-loading">Загружаем…</p>}
      {error && <p className="form-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="feed__empty">В этой группе пока нет постов</p>
      )}

      <div className="feed__list">
        {items.map((post) => (
          <PostCard key={post.id} post={post} />
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