"""Доменные исключения приложения.

Каждое исключение знает свой HTTP-статус, поэтому обработчик в
``app.handlers`` не разрастается при добавлении новых ошибок.
"""


class DomainException(Exception):
    """Базовое исключение бизнес-логики."""

    status_code: int = 400
    detail: str | None = None

    def __init__(self, detail: str | None = None):
        self.detail = detail or self.detail or self.__class__.__doc__ or "Ошибка"
        super().__init__(self.detail)


class NotFoundError(DomainException):
    status_code = 404
    detail = "Не найдено"


class ConflictError(DomainException):
    status_code = 409
    detail = "Конфликт данных"


class ForbiddenError(DomainException):
    status_code = 403
    detail = "Недостаточно прав"


class UnauthorizedError(DomainException):
    status_code = 401
    detail = "Требуется авторизация"


class ValidationError(DomainException):
    status_code = 422
    detail = "Некорректные данные"


class PayloadTooLargeError(DomainException):
    status_code = 413
    detail = "Файл слишком большой"


class UnsupportedMediaTypeError(DomainException):
    status_code = 415
    detail = "Неподдерживаемый формат файла"


# --- Конкретные ошибки ---


class PostNotFoundError(NotFoundError):
    detail = "Пост не найден"


class UserNotFoundError(NotFoundError):
    detail = "Пользователь не найден"


class GroupNotFoundError(NotFoundError):
    detail = "Сообщество не найдено"


class CommentNotFoundError(NotFoundError):
    detail = "Комментарий не найден"


class PermissionDeniedError(ForbiddenError):
    detail = "Недостаточно прав"


class NotGroupMemberError(ForbiddenError):
    detail = "Только участники группы могут это делать"


class CannotFollowSelfError(ValidationError):
    detail = "Нельзя подписаться на себя"


class UsernameAlreadyExistsError(ConflictError):
    detail = "Этот ник уже занят"


class GroupAlreadyExistsError(ConflictError):
    detail = "Группа с таким slug уже существует"


class AlreadyFollowingError(ConflictError):
    detail = "Вы уже подписаны на этого пользователя"
