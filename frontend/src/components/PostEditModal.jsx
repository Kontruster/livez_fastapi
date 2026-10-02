import { useEffect, useState } from 'react'
import Modal from './Modal'
import ImageUploader from './ImageUploader'
import { postsApi } from '../api/client'

export default function PostEditModal({ open, post, onClose, onSaved }) {
  const [text, setText] = useState('')
  const [images, setImages] = useState([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (open && post) {
      setText(post.text || '')
      setImages((post.images || []).map((i) => i.url))
      setError('')
    }
  }, [open, post])

  const onSubmit = async (e) => {
    e?.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError('')
    try {
      const updated = await postsApi.update(post.id, {
        text: text.trim(),
        image: images[0] || null,
        images,
      })
      onSaved(updated)
      onClose()
    } catch (err) {
      setError(err.message || 'Не удалось сохранить')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      title="Редактировать пост"
      onClose={busy ? () => { } : onClose}
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
            disabled={busy || !text.trim()}
          >
            {busy ? 'Сохраняем…' : 'Сохранить'}
          </button>
        </div>
      }
    >
      <form className="form-stack" onSubmit={onSubmit}>
        <label className="form-field">
          <span>Текст</span>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            rows={5}
            maxLength={2000}
            required
          />
        </label>

        <div className="form-field">
          <span>Картинка</span>
          <ImageUploader
            multiple
            values={images}
            onValuesChange={setImages}
            disabled={busy}
          />
        </div>

        {error && <p className="form-error">{error}</p>}
      </form>
    </Modal>
  )
}