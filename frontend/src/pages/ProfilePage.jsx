import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { profileApi, postsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import PostCard from '../components/PostCard'
import PostEditModal from '../components/PostEditModal'
import ConfirmDialog from '../components/ConfirmDialog'

export default function ProfilePage() {
  const { username } = useParams()
  const { user } = useAuth()
  const toast = useToast()

  const [profile, setProfile] = useState(null)
  const [posts, setPosts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [followBusy, setFollowBusy] = useState(false)

  const [editing, setEditing] = useState(null)
  const [pendingDelete, setPendingDelete] = useState(null)
  const [deleteBusy, setDeleteBusy] = useState(false)

  const isMe = !username || username === 'me' || username === user?.username

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError('')

    const req = isMe ? profileApi.me() : profileApi.byUsername(username)

    req
      .then((data) => {
        if (cancelled) return
        setProfile(data)
        setPosts(data.posts?.items || [])
      })
      .catch((err) => !cancelled && setError(err.message || 'Профиль не найден'))
      .finally(() => !cancelled && setLoading(false))

    return () => {
      cancelled = true
    }
  }, [username, isMe])

  const onFollowToggle = async () => {
    if (!profile) return
    setFollowBusy(true)
    const target = profile.author.username
    try {
      if (profile.is_following) {
        await profileApi.unfollow(target)
        toast.success(`Вы отписались от ${target}`)
      } else {
        await profileApi.follow(target)
        toast.success(`Вы подписались на ${target}`)
      }
      setProfile((p) => ({ ...p, is_following: !p.is_following }))
    } catch (err) {
      toast.error(err.message || 'Не удалось изменить подписку')
    } finally {
      setFollowBusy(false)
    }
  }

  const onSaved = (updated) => {
    setPosts((prev) => prev.map((p) => (p.id === updated.id ? updated : p)))
    toast.success('Пост обновлён')
  }

  const confirmDelete = async () => {
    if (!pendingDelete) return
    setDeleteBusy(true)
    try {
      await postsApi.remove(pendingDelete.id)
      setPosts((prev) => prev.filter((p) => p.id !== pendingDelete.id))
      setProfile((p) =>
        p ? { ...p, total_posts: Math.max(0, p.total_posts - 1) } : p,
      )
      toast.success('Пост удалён')
      setPendingDelete(null)
    } catch (err) {
      toast.error(err.message || 'Не удалось удалить')
    } finally {
      setDeleteBusy(false)
    }
  }

  if (loading) return <p className="page-loading">Загружаем профиль…</p>
  if (error) return <p className="form-error">{error}</p>
  if (!profile) return null

  const author = profile.author
  const canFollow = !isMe && user

  return (
    <div className="profile">
      <header className="profile__head">
        <div className="profile__avatar">
          {author.avatar_url ? (
            <img
              className="avatar-xs"
              src={author.avatar_url}
              alt=""
              loading="lazy"
            />
          ) : (
            <span className="avatar-xs">
              {(author.username || '?')[0].toUpperCase()}
            </span>
          )}
        </div>

        <div className="profile__info">
          <h1 className="profile__name">{author.username}</h1>
          <p className="profile__stats">
            {profile.total_posts}{' '}
            {profile.total_posts === 1
              ? 'пост'
              : profile.total_posts >= 2 && profile.total_posts <= 4
                ? 'поста'
                : 'постов'}
          </p>
        </div>

        {canFollow && (
          <button
            type="button"
            className={profile.is_following ? 'btn-ghost' : 'btn-primary'}
            onClick={onFollowToggle}
            disabled={followBusy}
          >
            {followBusy
              ? '…'
              : profile.is_following
                ? 'Отписаться'
                : 'Подписаться'}
          </button>
        )}

        {isMe && <span className="profile__badge">Это вы</span>}
      </header>

      <h2 className="profile__section-title">Посты</h2>

      {posts.length === 0 && (
        <p className="feed__empty">
          {isMe ? 'Вы ещё ничего не опубликовали' : 'Постов пока нет'}
        </p>
      )}

      <div className="feed__list">
        {posts.map((post) => (
          <PostCard
            key={post.id}
            post={post}
            isOwner={isMe}
            onEdit={setEditing}
            onDelete={setPendingDelete}
          />
        ))}
      </div>

      <p className="profile__hint">
        <Link to="/">← К ленте</Link>
      </p>

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