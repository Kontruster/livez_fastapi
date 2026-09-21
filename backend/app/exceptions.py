class DomainException(Exception):
    """Базовое исключение бизнес-логики"""
    pass

class PostNotFoundError(DomainException):
    pass

class UserNotFoundError(DomainException):
    pass

class GroupNotFoundError(DomainException):
    pass

class PermissionDeniedError(DomainException):
    pass

class CannotFollowSelfError(DomainException):
    pass
