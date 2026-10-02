import { useRef, useState } from 'react'
import { uploadsApi } from '../api/client'

const MAX_BYTES = 10 * 1024 * 1024

export default function ImageUploader({
    value,
    onChange,
    disabled,
    multiple = false,
    values = [],
    onValuesChange,
}) {
    const inputRef = useRef(null)
    const [busy, setBusy] = useState(false)
    const [error, setError] = useState('')
    const [dragOver, setDragOver] = useState(false)

    const isMulti = multiple && typeof onValuesChange === 'function'

    const upload = async (files) => {
        const list = Array.from(files || []).filter((f) =>
            f.type.startsWith('image/'),
        )
        if (list.length === 0) {
            setError('Только изображения')
            return
        }
        const big = list.find((f) => f.size > MAX_BYTES)
        if (big) {
            setError(`«${big.name}» больше 10 МБ`)
            return
        }
        setBusy(true)
        setError('')
        try {
            const urls = await Promise.all(
                list.map((f) => uploadsApi.postImage(f).then((r) => r.url)),
            )
            if (isMulti) {
                onValuesChange([...(values || []), ...urls])
            } else {
                onChange(urls[0])
            }
        } catch (err) {
            setError(err.message || 'Не удалось загрузить')
        } finally {
            setBusy(false)
        }
    }

    const onFileInput = (e) => {
        upload(e.target.files)
        e.target.value = ''
    }

    const onDrop = (e) => {
        e.preventDefault()
        setDragOver(false)
        if (disabled) return
        upload(e.dataTransfer.files)
    }

    const removeOne = (url) => {
        if (isMulti) {
            onValuesChange(values.filter((u) => u !== url))
        } else {
            onChange(null)
        }
    }

    const current = isMulti ? values || [] : value ? [value] : []

    return (
        <div
            className={
                'image-uploader' + (dragOver ? ' image-uploader--over' : '')
            }
            onDragOver={(e) => {
                e.preventDefault()
                if (!disabled) setDragOver(true)
            }}
            onDragLeave={() => setDragOver(false)}
            onDrop={onDrop}
        >
            <input
                ref={inputRef}
                type="file"
                accept="image/*"
                hidden
                multiple={multiple}
                onChange={onFileInput}
            />

            <div className="image-uploader__toolbar">
                <button
                    type="button"
                    className="btn-ghost btn-small"
                    onClick={() => inputRef.current?.click()}
                    disabled={disabled || busy}
                >
                    📎 {busy ? 'Загружаем…' : multiple ? 'Прикрепить картинки' : 'Прикрепить картинку'}
                </button>
                {current.length === 0 && (
                    <span className="image-uploader__hint">
                        или перетащите файл сюда · JPEG / PNG / WEBP / GIF, до 10 МБ
                    </span>
                )}
            </div>

            {current.length > 0 && (
                <div className="image-uploader__grid">
                    {current.map((url) => (
                        <div key={url} className="image-uploader__preview">
                            <img src={url} alt="" />
                            <button
                                type="button"
                                className="image-uploader__remove"
                                onClick={() => removeOne(url)}
                                disabled={disabled || busy}
                                aria-label="Убрать"
                            >
                                ×
                            </button>
                        </div>
                    ))}
                </div>
            )}

            {error && <p className="form-error" style={{ marginTop: 8 }}>{error}</p>}
        </div>
    )
}