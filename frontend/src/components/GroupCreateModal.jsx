import { useEffect, useState } from 'react'
import Modal from './Modal'
import { groupsApi } from '../api/client'

// Простая транслитерация для автозаполнения slug из title.
const TRANSLIT = {
  а:'a', б:'b', в:'v', г:'g', д:'d', е:'e', ё:'e', ж:'zh', з:'z',
  и:'i', й:'y', к:'k', л:'l', м:'m', н:'n', о:'o', п:'p', р:'r',
  с:'s', т:'t', у:'u', ф:'f', х:'h', ц:'c', ч:'ch', ш:'sh', щ:'sch',
  ъ:'', ы:'y', ь:'', э:'e', ю:'yu', я:'ya',
}

function slugify(input) {
  return input
    .toLowerCase()
    .split('')
    .map((ch) => (TRANSLIT[ch] !== undefined ? TRANSLIT[ch] : ch))
    .join('')
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 64)
}

export default function GroupCreateModal({ open, onClose, onCreated }) {
  const [title, setTitle] = useState('')
  const [slug, setSlug] = useState('')
  const [slugTouched, setSlugTouched] = useState(false)
  const [description, setDescription] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) {
      setTitle('')
      setSlug('')
      setSlugTouched(false)
      setDescription('')
      setError('')
    }
  }, [open])

  useEffect(() => {
    if (!slugTouched) setSlug(slugify(title))
  }, [title, slugTouched])

  const onSubmit = async (e) => {
    e?.preventDefault()
    if (!title.trim() || !slug.trim()) return
    setBusy(true)
    setError('')
    try {
      const created = await groupsApi.create({
        title: title.trim(),
        slug: slug.trim(),
        description: description.trim(),
      })
      onCreated(created)
      onClose()
    } catch (err) {
      setError(err.message || 'Не удалось создать группу')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Новая группа"
      onClose={busy ? () => {} : onClose}
      footer={
        <div className="modal__actions">
          <button
            type="button"
            className="btn-ghost"
            onClick={onClose}
            disabled={busy}
          >
            Отмена
          </button>
          <button
            type="button"
            className="btn-primary"
            onClick={onSubmit}
            disabled={busy || !title.trim() || !slug.trim()}
          >
            {busy ? 'Создаём…' : 'Создать'}
          </button>
        </div>
      }
    >
      <form className="form-stack" onSubmit={onSubmit}>
        <label className="form-field">
          <span>Название</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Например, Программирование"
            maxLength={200}
            required
            autoFocus
          />
        </label>

        <label className="form-field">
          <span>Slug (часть URL)</span>
          <input
            value={slug}
            onChange={(e) => {
              setSlugTouched(true)
              setSlug(e.target.value)
            }}
            placeholder="programmirovanie"
            maxLength={64}
            required
          />
          <small className="form-hint">
            URL группы: /groups/<b>{slug || '…'}</b>
          </small>
        </label>

        <label className="form-field">
          <span>Описание</span>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={3}
            placeholder="О чём эта группа?"
          />
        </label>

        {error && <p className="form-error">{error}</p>}
      </form>
    </Modal>
  )
}