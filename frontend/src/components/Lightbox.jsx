import { useCallback, useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'

export default function Lightbox({
  open,
  images = [],
  index = 0,
  onIndexChange,
  onClose,
}) {
  const touchStartX = useRef(null)
  const wheelLock = useRef(false)

  const goNext = useCallback(() => {
    if (index < images.length - 1) onIndexChange(index + 1)
  }, [index, images.length, onIndexChange])

  const goPrev = useCallback(() => {
    if (index > 0) onIndexChange(index - 1)
  }, [index, onIndexChange])

  // Клавиатура
  useEffect(() => {
    if (!open) return
    const onKey = (e) => {
      if (e.key === 'Escape') onClose()
      if (e.key === 'ArrowRight') goNext()
      if (e.key === 'ArrowLeft') goPrev()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, goNext, goPrev, onClose])

  // Скролл (тачпад, колёсико)
  const onWheel = (e) => {
    if (wheelLock.current) return
    const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY
    if (Math.abs(delta) < 15) return
    wheelLock.current = true
    if (delta > 0) goNext()
    else goPrev()
    setTimeout(() => {
      wheelLock.current = false
    }, 350)
  }

  // Тач — свайп влево/вправо
  const onTouchStart = (e) => {
    touchStartX.current = e.touches[0].clientX
  }
  const onTouchEnd = (e) => {
    if (touchStartX.current == null) return
    const dx = e.changedTouches[0].clientX - touchStartX.current
    touchStartX.current = null
    if (Math.abs(dx) < 50) return
    if (dx < 0) goNext()
    else goPrev()
  }

  if (!open || images.length === 0) return null

  const src = images[index]

  return createPortal(
    <div className="lightbox-backdrop" onClick={onClose}>
      <div
        className="lightbox"
        onClick={(e) => e.stopPropagation()}
        onWheel={onWheel}
        onTouchStart={onTouchStart}
        onTouchEnd={onTouchEnd}
      >
        {/* Клик по левой трети — назад */}
        {index > 0 && (
          <div
            className="lightbox__zone lightbox__zone--prev"
            onClick={goPrev}
            aria-label="Предыдущая"
          >
            <span className="lightbox__zone-arrow">‹</span>
          </div>
        )}

        <img
          key={src}
          className="lightbox__image"
          src={src}
          alt=""
          draggable={false}
        />

        {/* Клик по правой трети — вперёд */}
        {index < images.length - 1 && (
          <div
            className="lightbox__zone lightbox__zone--next"
            onClick={goNext}
            aria-label="Следующая"
          >
            <span className="lightbox__zone-arrow">›</span>
          </div>
        )}

        <button
          type="button"
          className="lightbox__close"
          onClick={onClose}
          aria-label="Закрыть"
        >
          ×
        </button>

        {images.length > 1 && (
          <div className="lightbox__counter">
            {index + 1} / {images.length}
          </div>
        )}
      </div>
    </div>,
    document.body,
  )
}