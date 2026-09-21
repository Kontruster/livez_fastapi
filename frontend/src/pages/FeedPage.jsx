import { useEffect, useState } from 'react'
import { postsApi, groupsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import PostCard from '../components/PostCard'
import PostForm from '../components/PostForm'
import PostEditModal from '../components/PostEditModal'
import ConfirmDialog from '../components/ConfirmDialog'

const SIZE = 10

export default function FeedPage() {
  const { user } = useAuth()
  const toast = useToast()

  const [tab, setTab] = useState('all')
  const [q, setQ] = useState('')
  const [query, setQuery] = useState('')

  const [page, setPage] = useState(1)
  const [items, setItems] = useState([])
  const [pages, setPages] = useState(1)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const [groups, setGroups] = useState([])

  // редактирование
  const [editing, setEditing] = useState(null)
  // удаление
  const [pendingDelete, setPendingDelete] = useState(null)
  const [deleteBusy, setDeleteBusy] = useState(false)

  useEffect(() => {
    groupsApi.list().then(setGroups).catch(() => {})
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    const loader =
      tab === 'follow'
        ? postsApi.followFeed({ page, size: SIZE })
        : postsApi.feed({ page, size: SIZE, q: query })

    loader
      .then((data) => {
        if (cancelled) return
        setItems(data.items || [])
        setPages(data.pages || 1)
      })
      .catch((err) => {
        if (cancelled) return
        setError(err.message || 'Не удалось загрузить ленту')
      })
      .finally(() => !cancelled && setLoading(false))

    return () => {
      cancelled = true
    }
  }, [tab, page, query])

  const switchTab = (next) => {
    if (next === tab) return
    setTab(next)
    setPage(1)
  }

  const onSubmitSearch = (e) => {
    e.preventDefault()
    setPage(1)
    setQuery(q.trim())
  }

  const onCreated = (created) => {
    if (page === 1) setItems((prev) => [created, ...prev])
    toast.success('Пост опубликован')
  }

  const onSaved = (updated) => {
    setItems((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
    toast.success('Пост обновлён')
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    setDeleteBusy(true)
    try {
      await postsApi.remove(pendingDelete.id)
      setItems((prev) => prev.filter((p) => p.id !== pendingDelete.id))
      toast.success('Пост удалён')
      setPendingDelete(null)
    } catch (err) {
      toast.error(err.message || 'Не удалось удалить')
    } finally {
      setDeleteBusy(false)
    }
  }

  const isOwner = (post) =>
    !!user &&
    (post.author?.id === user.id || post.author_id === user.id)

  return (
    <div className="feed">
      <PostForm groups={groups} onCreated={onCreated} />

      <div className="feed__tabs">
        <button
          type="button"
          className={tab === 'all' ? 'tab tab--active' : 'tab'}
          onClick={() => switchTab('all')}
        >
          Все посты
        </button>
        <button
          type="button"
          className={tab === 'follow' ? 'tab tab--active' : 'tab'}
          onClick={() => switchTab('follow')}
          disabled={!user}
        >
          Мои подписки
        </button>
      </div>

      {tab === 'all' && (
        <form className="feed__search" onSubmit={onSubmitSearch}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Поиск по тексту…"
          />
          <button type="submit">Найти</button>
          {query && (
            <button
              type="button"
              className="btn-ghost btn-small"
              onClick={() => {
                setQ('')
                setQuery('')
                setPage(1)
              }}
            >
              Сбросить
            </button>
          )}
        </form>
      )}

      {loading && <p className="page-loading">Загружаем…</p>}
      {error && <p className="form-error">{error}</p>}

      {!loading && !error && items.length === 0 && (
        <p className="feed__empty">
          {query
            ? 'Ничего не найдено'
            : tab === 'follow'
              ? 'Вы пока ни на кого не подписаны'
              : 'Постов пока нет — напишите первый!'}
        </p>
      )}

      <div className="feed__list">
        {items.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            isOwner={isOwner(post)}
            onEdit={setEditing}
            onDelete={setPendingDelete}
          />
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

      <PostEditModal
        open={!!editing}
        post={editing}
        onClose={() => setEditing(null)}
        onSaved={onSaved}
      />

      <ConfirmDialog
        open={!!pendingDelete}
        title="Удалить пост?"
        message="Это действие нельзя отменить."
        confirmLabel="Удалить"
        danger
        busy={deleteBusy}
        onConfirm={confirmDelete}
        onClose={() => setPendingDelete(null)}
      />
    </div>
  )
}