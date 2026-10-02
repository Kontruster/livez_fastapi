import { useNavigate, Link } from 'react-router-dom'
import { useState } from 'react'
import Lightbox from './Lightbox'

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  return d.toLocaleString('ru-RU', {
    day: 'numeric', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function PostCard({ post, isOwner, onEdit, onDelete }) {
  const author = post.author || post.user || {}
  const group = post.group
  const commentsCount = post.comments_count ?? post.comments?.length
  const navigate = useNavigate()
  const [lightboxIndex, setLightboxIndex] = useState(null)
  const urls = post.images?.length > 0
    ? post.images.map((i) => i.url)
    : post.image
      ? [post.image]
      : []


  return (
    <article className="post-card">
      <header className="post-card__head">
        <div className="post-card__author">
          {author.avatar_url ? (
            <img className="avatar-xs" src={author.avatar_url} alt="" />
          ) : (
            <span className="avatar-xs">
              {(author.username || '?')[0].toUpperCase()}
            </span>
          )}
          {author.username ? (
            <Link to={`/profile/${author.username}`} className="post-card__name">
              {author.username}
            </Link>
          ) : (
            <span className="post-card__name">Аноним</span>
          )}
          {group && (
            <>
              <span className="post-card__sep">·</span>
              <Link to={`/groups/${group.slug}`} className="post-card__group">
                {group.title || group.slug}
              </Link>
            </>
          )}
        </div>
        <time className="post-card__date">{formatDate(post.pub_date)}</time>
      </header>

      {/* <Link to={`/posts/${post.id}`} className="post-card__text-link">
        {post.text && <p className="post-card__text">{post.text}</p>}
      </Link> */}

      {post.text && (
        <p
          className="post-card__text post-card__text--clickable"
          onClick={() => navigate(`/posts/${post.id}`)}
          role="link"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter') navigate(`/posts/${post.id}`)
          }}
        >
          {post.text}
        </p>
      )}

      {urls.length > 0 && (
        <div className="post-card__gallery">
          {urls.map((url, i) => (
            <button
              key={url}
              type="button"
              className="post-card__gallery-item"
              onClick={() => setLightboxIndex(i)}
            >
              <img src={url} alt="" loading="lazy" />
            </button>
          ))}
        </div>
      )}

      <Lightbox
        open={lightboxIndex !== null}
        images={urls}
        index={lightboxIndex ?? 0}
        onIndexChange={setLightboxIndex}
        onClose={() => setLightboxIndex(null)}
      />

      <footer className="post-card__foot">
        <Link to={`/posts/${post.id}`} className="post-card__comments-link">
          💬 {commentsCount != null ? commentsCount : 'Комментарии'}
        </Link>

        {isOwner && (
          <div className="post-card__actions">
            {onEdit && (
              <button
                type="button"
                className="btn-ghost btn-small"
                onClick={() => onEdit(post)}
              >
                Редактировать
              </button>
            )}
            {onDelete && (
              <button
                type="button"
                className="btn-ghost btn-small btn-danger-ghost"
                onClick={() => onDelete(post)}
              >
                Удалить
              </button>
            )}
          </div>
        )}
      </footer>
    </article>
  )
}