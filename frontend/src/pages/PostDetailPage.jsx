import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { postsApi } from '../api/client'
import CommentList from '../components/CommentList'
import LikeButton from '../components/LikeButton'
import { addReply, countComments, removeComment } from '../utils/commentTree'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
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

  const onCommentAdded = (created, parentId) => {
    setComments((prev) => addReply(prev, parentId, created))
    setPost((p) => (p ? { ...p, comments_count: (p.comments_count || 0) + 1 } : p))
  }

  const onCommentDeleted = (commentId) => {
    // сначала считаем, сколько узлов уйдёт вместе с поддеревом
    const removed = (function countRemoved(tree) {
      for (const node of tree) {
        if (node.id === commentId) return countComments([node])
        const found = countRemoved(node.replies || [])
        if (found) return found
      }
      return 0
    })(comments)

    setComments((prev) => removeComment(prev, commentId))
    setPost((p) =>
      p ? { ...p, comments_count: Math.max(0, (p.comments_count || 0) - removed) } : p,
    )
  }

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
              {group.is_private && <span className="badge-private">приватная</span>}
            </Link>
          </>
        )}
        <time className="post-detail__date">{formatDate(post.pub_date)}</time>
      </header>

      {post.text && <p className="post-detail__text">{post.text}</p>}
      {post.images?.length > 0 ? (
        <div className="post-detail__gallery">
          {post.images.map((img) => (
            <img
              key={img.id}
              className="post-detail__image"
              src={img.url}
              alt=""
              loading="lazy"
            />
          ))}
        </div>
      ) : post.image ? (
        <img className="post-detail__image" src={post.image} alt="" />
      ) : null}

      <div className="post-detail__reactions">
        <LikeButton
          post={post}
          onChange={(state) => setPost((p) => (p ? { ...p, ...state } : p))}
        />
      </div>

      <CommentList
        postId={post.id}
        comments={comments}
        onAdded={onCommentAdded}
        onDeleted={onCommentDeleted}
      />
    </article>
  )
}
