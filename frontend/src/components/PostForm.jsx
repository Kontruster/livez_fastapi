import { useState } from 'react'
import { postsApi } from '../api/client'

// Группы грузим один раз и передаём сверху — они редко меняются.
// Если не хочешь возиться — просто не передавай groups, форма всё равно работает.
export default function PostForm({ groups = [], onCreated }) {
  const [text, setText] = useState('')
  const [groupId, setGroupId] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  const onSubmit = async (e) => {
    e.preventDefault()
    if (!text.trim()) return
    setBusy(true)
    setError('')
    try {
      const payload = { text: text.trim() }
      if (groupId) payload.group_id = Number(groupId)
      const created = await postsApi.create(payload)
      setText('')
      setGroupId('')
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
        placeholder="О чём думаешь?"
        value={text}
        onChange={(e) => setText(e.target.value)}
        rows={3}
        maxLength={2000}
        required
      />

      <div className="post-form__row">
        {groups.length > 0 && (
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