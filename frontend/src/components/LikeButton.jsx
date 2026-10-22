import { useEffect, useState } from 'react'
import { postsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'

export default function LikeButton({ post, onChange, showCount = true }) {
  const { user } = useAuth()
  const [liked, setLiked] = useState(!!post.is_liked)
  const [count, setCount] = useState(post.likes_count ?? 0)
  const [busy, setBusy] = useState(false)

  // если пост обновился снаружи (например, лента перезагрузилась)
  useEffect(() => {
    setLiked(!!post.is_liked)
    setCount(post.likes_count ?? 0)
  }, [post.id, post.is_liked, post.likes_count])

  const toggle = async () => {
    if (!user || busy) return

    const prevLiked = liked
    const prevCount = count
    const nextLiked = !liked

    setLiked(nextLiked)
    setCount(Math.max(0, prevCount + (nextLiked ? 1 : -1)))
    setBusy(true)

    try {
      const res = nextLiked
        ? await postsApi.like(post.id)
        : await postsApi.unlike(post.id)
      setLiked(res.liked)
      setCount(res.likes_count)
      onChange?.({ is_liked: res.liked, likes_count: res.likes_count })
    } catch {
      // откат оптимистичного изменения
      setLiked(prevLiked)
      setCount(prevCount)
    } finally {
      setBusy(false)
    }
  }

  return (
    <button
      type="button"
      className={
        'like-button' +
        (liked ? ' like-button--active' : '') +
        (busy ? ' like-button--busy' : '')
      }
      onClick={toggle}
      disabled={!user || busy}
      title={user ? 'Нравится' : 'Войдите, чтобы поставить лайк'}
      aria-pressed={liked}
      aria-label={liked ? 'Убрать лайк' : 'Поставить лайк'}
    >
      <span className="like-button__icon">{liked ? '♥' : '♡'}</span>
      {showCount && <span className="like-button__count">{count}</span>}
    </button>
  )
}
