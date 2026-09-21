import Modal from './Modal'

export default function ConfirmDialog({
  open,
  title = 'Подтвердите действие',
  message,
  confirmLabel = 'Подтвердить',
  danger = false,
  busy = false,
  onConfirm,
  onClose,
}) {
  return (
    <Modal
      open={open}
      title={title}
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
            className={danger ? 'btn-danger' : 'btn-primary'}
            onClick={onConfirm}
            disabled={busy}
          >
            {busy ? '…' : confirmLabel}
          </button>
        </div>
      }
    >
      {message && <p className="confirm__message">{message}</p>}
    </Modal>
  )
}