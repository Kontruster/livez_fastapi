import { useState } from 'react'
import { Link } from 'react-router-dom'
import { postsApi } from '../api/client'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  })
}

export default function CommentList({ postId, comments = [], onAdded }) {
  const [text, setText] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError('')
    try {
      const created = await postsApi.addComment(postId, text.trim())
      setText('')
      onAdded?.(created)
    } catch (err) {
      setError(err.message || 'Не удалось отправить')
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="comments">
      <h2 className="comments__title">
        Комментарии {comments.length > 0 && `(${comments.length})`}
      </h2>

      <ul className="comments__list">
        {comments.length === 0 && (
          <li className="comments__empty">Пока никто не комментировал</li>
        )}
        {comments.map((c) => {
          const author = c.author || c.user || {}
          return (
            <li key={c.id} className="comment">
              <div className="comment__head">
                {author.username ? (
                  <Link
                    to={`/profile/${author.username}`}
                    className="comment__author"
                  >
                    {author.username}
                  </Link>
                ) : (
                  <span className="comment__author">Аноним</span>
                )}
                <time className="comment__date">{formatDate(c.pub_date)}</time>
              </div>
              <p className="comment__text">{c.text}</p>
            </li>
          )
        })}
      </ul>

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

      {error && <p className="form-error">{error}</p>}
    </section>
  )
}