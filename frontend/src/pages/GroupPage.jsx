import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { postsApi } from '../api/client'
import PostCard from '../components/PostCard'

const SIZE = 10

export default function GroupPage() {
  const { slug } = useParams()

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
        setItems(data.items || [])
        setPages(data.pages || 1)
      })
      .catch((err) => !cancelled && setError(err.message || 'Группа не найдена'))
      .finally(() => !cancelled && setLoading(false))

    return () => {
      cancelled = true
    }
  }, [slug, page])

  return (
    <div className="group-page">
      <Link to="/groups" className="profile__hint">
        ← Ко всем группам
      </Link>

      <h1 className="page-title">@{slug}</h1>

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