import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { accountApi } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import Modal from '../components/Modal'

export default function SettingsPage() {
  const { user, setUser, logout } = useAuth()
  const toast = useToast()
  const navigate = useNavigate()

  // --- username ---
  const [username, setUsername] = useState(user?.username || '')
  const [usernameBusy, setUsernameBusy] = useState(false)

  const saveUsername = async (e) => {
    e.preventDefault()
    if (username === user.username) return
    setUsernameBusy(true)
    try {
      const updated = await accountApi.changeUsername(username)
      setUser(updated)
      toast.success('Ник изменён')
    } catch (err) {
      toast.error(err.message || 'Не удалось изменить ник')
    } finally {
      setUsernameBusy(false)
    }
  }

  // --- аватар ---
  const fileInputRef = useRef(null)
  const [avatarBusy, setAvatarBusy] = useState(false)

  const onPickAvatar = () => fileInputRef.current?.click()

  const onAvatarSelected = async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setAvatarBusy(true)
    try {
      const updated = await accountApi.uploadAvatar(file)
      setUser(updated)
      toast.success('Аватар обновлён')
    } catch (err) {
      toast.error(err.message || 'Не удалось загрузить аватар')
    } finally {
      setAvatarBusy(false)
      e.target.value = ''
    }
  }

  // --- пароль ---
  const [oldPassword, setOldPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newPassword2, setNewPassword2] = useState('')
  const [passBusy, setPassBusy] = useState(false)

  const changePassword = async (e) => {
    e.preventDefault()
    if (newPassword !== newPassword2) {
      toast.error('Пароли не совпадают')
      return
    }
    if (newPassword.length < 6) {
      toast.error('Пароль минимум 6 символов')
      return
    }
    setPassBusy(true)
    try {
      await accountApi.changePassword(oldPassword, newPassword)
      toast.success('Пароль изменён')
      setOldPassword(''); setNewPassword(''); setNewPassword2('')
    } catch (err) {
      toast.error(err.message || 'Не удалось изменить пароль')
    } finally {
      setPassBusy(false)
    }
  }

  // --- удаление аккаунта ---
  const [confirmOpen, setConfirmOpen] = useState(false)
  const [deletePass, setDeletePass] = useState('')
  const [deleteBusy, setDeleteBusy] = useState(false)

  const deleteAccount = async () => {
    setDeleteBusy(true)
    try {
      await accountApi.deleteAccount(deletePass)
      setUser(null)
      toast.success('Аккаунт удалён')
      navigate('/login', { replace: true })
    } catch (err) {
      toast.error(err.message || 'Не удалось удалить аккаунт')
      setDeleteBusy(false)
    }
  }

  const initial = (user?.username || user?.email || '?')[0].toUpperCase()

  return (
    <div className="settings">
      <h1 className="page-title">Настройки аккаунта</h1>

      {/* --- Профиль --- */}
      <section className="settings__section">
        <h2 className="settings__section-title">Профиль</h2>

        <div className="settings__avatar-row">
          <div className="settings__avatar">
            {user?.avatar_url ? (
              <img src={user.avatar_url} alt="" />
            ) : (
              <span>{initial}</span>
            )}
          </div>
          <div>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={onAvatarSelected}
            />
            <button
              type="button"
              className="btn-ghost"
              onClick={onPickAvatar}
              disabled={avatarBusy}
            >
              {avatarBusy ? 'Загружаем…' : 'Сменить аватар'}
            </button>
            <p className="settings__hint">JPEG / PNG / WEBP / GIF, до 5 МБ</p>
          </div>
        </div>

        <form className="form-stack" onSubmit={saveUsername}>
          <label className="form-field">
            <span>Ник</span>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              minLength={3}
              maxLength={64}
              required
            />
          </label>
          <div>
            <button
              type="submit"
              className="btn-primary"
              disabled={usernameBusy || username === user?.username}
            >
              {usernameBusy ? 'Сохраняем…' : 'Сохранить ник'}
            </button>
          </div>
        </form>
      </section>

      {/* --- Пароль --- */}
      <section className="settings__section">
        <h2 className="settings__section-title">Смена пароля</h2>
        <form className="form-stack" onSubmit={changePassword}>
          <label className="form-field">
            <span>Текущий пароль</span>
            <input
              type="password"
              value={oldPassword}
              onChange={(e) => setOldPassword(e.target.value)}
              required
              autoComplete="current-password"
            />
          </label>
          <label className="form-field">
            <span>Новый пароль</span>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          <label className="form-field">
            <span>Повторите новый пароль</span>
            <input
              type="password"
              value={newPassword2}
              onChange={(e) => setNewPassword2(e.target.value)}
              required
              minLength={6}
              autoComplete="new-password"
            />
          </label>
          <div>
            <button type="submit" className="btn-primary" disabled={passBusy}>
              {passBusy ? 'Меняем…' : 'Сменить пароль'}
            </button>
          </div>
        </form>
      </section>

      {/* --- Опасная зона --- */}
      <section className="settings__section settings__section--danger">
        <h2 className="settings__section-title">Удаление аккаунта</h2>
        <p className="settings__hint">
          Все ваши посты, комментарии и подписки будут удалены безвозвратно.
        </p>
        <button
          type="button"
          className="btn-danger"
          onClick={() => {
            setDeletePass('')
            setConfirmOpen(true)
          }}
        >
          Удалить аккаунт
        </button>
      </section>

        <Modal
            open={confirmOpen}
            title="Удалить аккаунт?"
            onClose={() => !deleteBusy && setConfirmOpen(false)}
            footer={
                <div className="modal__actions">
                    <button
                        type="button"
                        className="btn-ghost"
                        onClick={() => setConfirmOpen(false)}
                        disabled={deleteBusy}
                    >
                        Отмена
                    </button>
                    <button
                        type="button"
                        className="btn-danger"
                        onClick={deleteAccount}
                        disabled={deleteBusy || !deletePass}
                    >
                        {deleteBusy ? 'Удаляем…' : 'Удалить навсегда'}
                    </button>
                </div>
            }
        >
            <p className="confirm__message">
                Это действие необратимо. Все ваши посты, комментарии и подписки
                будут удалены. Введите пароль для подтверждения.
            </p>
            <label className="form-field" style={{ marginTop: 12 }}>
                <span>Пароль</span>
                <input
                    type="password"
                    value={deletePass}
                    onChange={(e) => setDeletePass(e.target.value)}
                    autoComplete="current-password"
                />
            </label>
        </Modal>
    </div>
  )
}