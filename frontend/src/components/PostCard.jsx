import { Link } from 'react-router-dom'

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

      <Link to={`/posts/${post.id}`} className="post-card__body">
        {post.text && <p className="post-card__text">{post.text}</p>}
        {post.image && (
          <img className="post-card__image" src={post.image} alt="" loading="lazy" />
        )}
      </Link>

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