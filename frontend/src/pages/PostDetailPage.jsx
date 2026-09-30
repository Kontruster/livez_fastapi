import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { postsApi } from '../api/client'
import CommentList from '../components/CommentList'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PostDetailPage() {
  const { id } = useParams()
  const [post, setPost] = useState(null)
  const [comments, setComments] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    postsApi
      .detail(id)
      .then((data) => {
        if (cancelled) return
        const payload = data.post ? data.post : data
        const cmts = data.comments ?? payload.comments ?? []
        setPost(payload)
        setComments(cmts)
      })
      .catch((err) => !cancelled && setError(err.message || 'Не найдено'))
      .finally(() => !cancelled && setLoading(false))
    return () => {
      cancelled = true
    }
  }, [id])

  if (loading) return <p className="page-loading">Загружаем пост…</p>
  if (error) return <p className="form-error">{error}</p>
  if (!post) return null

  const author = post.author || post.user || {}
  const group = post.group

  return (
    <article className="post-detail">
      <Link to="/" className="post-detail__back">
        ← К ленте
      </Link>

      <header className="post-detail__head">
        {author.username ? (
          <Link to={`/profile/${author.username}`} className="post-detail__author">
            {author.username}
          </Link>
        ) : (
          <span className="post-detail__author">Аноним</span>
        )}
        {group && (
          <>
            <span className="post-card__sep">·</span>
            <Link to={`/groups/${group.slug}`} className="post-card__group">
              {group.title || group.slug}
            </Link>
          </>
        )}
        <time className="post-detail__date">{formatDate(post.pub_date)}</time>
      </header>

      {post.text && <p className="post-detail__text">{post.text}</p>}
      {post.image && (
        <img className="post-detail__image" src={post.image} alt="" />
      )}

      <CommentList
        postId={post.id}
        comments={comments}
        onAdded={(c) => setComments((prev) => [...prev, c])}
      />
    </article>
  )
}