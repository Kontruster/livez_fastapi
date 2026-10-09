import { useState } from 'react'
import { Link } from 'react-router-dom'
import { postsApi } from '../api/client'
import { useAuth } from '../context/AuthContext'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function countReplies(replies) {
  return (replies || []).reduce((sum, r) => sum + 1 + countReplies(r.replies), 0)
}

function Avatar({ author }) {
  if (author?.avatar_url) {
    return <img className="avatar-xs" src={author.avatar_url} alt="" />
  }
  return <span className="avatar-xs">{(author?.username || '?')[0].toUpperCase()}</span>
}

function CommentItem({ comment, postId, depth, onAdded, onDeleted }) {
  const { user } = useAuth()
  const [replying, setReplying] = useState(false)
  const [replyText, setReplyText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const author = comment.author || {}
  const isOwner = !!user && author.id === user.id
  const replies = comment.replies || []

  const submitReply = async (e) => {
    e.preventDefault()
    const text = replyText.trim()
    if (!text) return
    setBusy(true)
    setError('')
    try {
      const created = await postsApi.addComment(postId, text, comment.id)
      onAdded?.(created, comment.id)
      setReplyText('')
      setReplying(false)
    } catch (err) {
      setError(err.message || 'Не удалось ответить')
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    setBusy(true)
    setError('')
    try {
      await postsApi.removeComment(comment.id)
      onDeleted?.(comment.id)
    } catch (err) {
      setError(err.message || 'Не удалось удалить')
      setBusy(false)
    }
  }

  return (
    <li className="comment" style={{ '--depth': Math.min(depth, 4) }}>
      <div className="comment__head">
        <Avatar author={author} />
        {author.username ? (
          <Link to={`/profile/${author.username}`} className="comment__author">
            {author.username}
          </Link>
        ) : (
          <span className="comment__author">Аноним</span>
        )}
        <time className="comment__date">{formatDate(comment.pub_date)}</time>
      </div>

      <p className="comment__text">{comment.text}</p>

      <div className="comment__actions">
        {user && (
          <button
            type="button"
            className="btn-ghost btn-small"
            onClick={() => setReplying((v) => !v)}
            disabled={busy}
          >
            {replying ? 'Отмена' : 'Ответить'}
          </button>
        )}
        {isOwner && (
          <button
            type="button"
            className="btn-ghost btn-small btn-danger-ghost"
            onClick={remove}
            disabled={busy}
          >
            {busy ? '…' : 'Удалить'}
          </button>
        )}
      </div>

      {replying && (
        <form className="comment-form comment-form--reply" onSubmit={submitReply}>
          <input
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder={`Ответить ${author.username || ''}…`}
            maxLength={300}
            autoFocus
          />
          <button type="submit" disabled={busy || !replyText.trim()}>
            {busy ? '…' : 'Отправить'}
          </button>
        </form>
      )}

      {error && <p className="form-error">{error}</p>}

      {replies.length > 0 && (
        <ul className="comments__list comments__list--nested">
          {replies.map((child) => (
            <CommentItem
              key={child.id}
              comment={child}
              postId={postId}
              depth={depth + 1}
              onAdded={onAdded}
              onDeleted={onDeleted}
            />
          ))}
        </ul>
      )}
    </li>
  )
}

export default function CommentList({ postId, comments = [], onAdded, onDeleted }) {
  const { user } = useAuth()
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const total = countReplies(comments)

  const onSubmit = async (e) => {
    e.preventDefault()
    const value = text.trim()
    if (!value) return
    setBusy(true)
    setError('')
    try {
      const created = await postsApi.addComment(postId, value)
      setText('')
      onAdded?.(created, null)
    } catch (err) {
      setError(err.message || 'Не удалось отправить')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="comments">
      <h2 className="comments__title">Комментарии {total > 0 && `(${total})`}</h2>

      <ul className="comments__list">
        {comments.length === 0 && (
          <li className="comments__empty">Пока никто не комментировал</li>
        )}
        {comments.map((c) => (
          <CommentItem
            key={c.id}
            comment={c}
            postId={postId}
            depth={0}
            onAdded={onAdded}
            onDeleted={onDeleted}
          />
        ))}
      </ul>

      {user ? (
        <form className="comment-form" onSubmit={onSubmit}>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Написать комментарий…"
            maxLength={300}
          />
          <button type="submit" disabled={busy || !text.trim()}>
            {busy ? '…' : 'Отправить'}
          </button>
        </form>
      ) : (
        <p className="comments__login-hint">
          <Link to="/login">Войдите</Link>, чтобы оставить комментарий
        </p>
      )}

      {error && <p className="form-error">{error}</p>}
    </section>
  )
}
