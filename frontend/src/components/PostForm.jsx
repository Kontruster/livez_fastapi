import { useEffect, useState } from 'react'
import { postsApi } from '../api/client'
import ImageUploader from './ImageUploader'

export default function PostForm({
  groups = [],
  fixedGroupId,
  onCreated,
}) {
  const [text, setText] = useState('')
  const [images, setImages] = useState([]);
  const [groupId, setGroupId] = useState(
    fixedGroupId ? String(fixedGroupId) : '',
  )
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (fixedGroupId) setGroupId(String(fixedGroupId))
  }, [fixedGroupId])

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError('')
    try {
      const payload = { text: text.trim() }
      if (groupId) payload.group_id = Number(groupId)
      if (images.length > 0) {
        payload.image = images[0]
        payload.images = images
      }
      const created = await postsApi.create(payload)
      setText('')
      setImages([])
      if (!fixedGroupId) setGroupId('')
      onCreated?.(created)
    } catch (err) {
      setError(err.message || 'Не удалось создать пост')
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="post-form" onSubmit={onSubmit}>
      <textarea
        className="post-form__text"
        placeholder={
          fixedGroupId ? 'Написать в эту группу…' : 'О чём думаешь?'
        }
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        maxLength={2000}
        required
      />

      <ImageUploader
        multiple
        values={images}
        onValuesChange={setImages}
        disabled={busy}
      />

      <div className="post-form__row">
        {!fixedGroupId && groups.length > 0 && (
          <select
            className="post-form__select"
            value={groupId}
            onChange={(e) => setGroupId(e.target.value)}
          >
            <option value="">Без группы</option>
            {groups.map((g) => (
              <option key={g.id} value={g.id}>
                {g.title}
              </option>
            ))}
          </select>
        )}

        <button
          type="submit"
          className="btn-primary"
          disabled={busy || !text.trim()}
        >
          {busy ? 'Публикуем…' : 'Опубликовать'}
        </button>
      </div>

      {error && <p className="form-error">{error}</p>}
    </form>
  )
}