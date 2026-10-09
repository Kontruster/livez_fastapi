"""Централизованные обработчики ошибок.

Роутеры больше не ловят исключения вручную: любое доменное исключение
превращается в ответ с корректным статусом, а неожиданные ошибки —
в 500 с записью в лог без утечки деталей наружу.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.exceptions import ConflictError, DomainException

logger = logging.getLogger(__name__)


def _safe_errors(errors: list[dict]) -> list[dict]:
    """Приводит ошибки валидации к JSON-сериализуемому виду.

    ``exc.errors()`` может содержать несериализуемые объекты (например,
    исходный ``ValueError`` в поле ``ctx``), из-за чего ответ падал с 500.
    """
    safe = []
    for err in errors:
        safe.append(
            {
                "loc": [str(part) for part in err.get("loc", ())],
                "msg": str(err.get("msg", "")),
                "type": str(err.get("type", "")),
            }
        )
    return safe


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request: Request, exc: DomainException):
        if exc.status_code >= 500:
            logger.exception("Доменная ошибка: %s", exc)
        else:
            logger.info(
                "%s %s -> %s: %s", request.method, request.url.path, exc.status_code, exc.detail
            )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(IntegrityError)
    async def integrity_error_handler(request: Request, exc: IntegrityError):
        logger.warning(
            "Нарушение целостности БД на %s %s: %s",
            request.method,
            request.url.path,
            exc.orig,
        )
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Конфликт данных: запись уже существует"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": _safe_errors(exc.errors())},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Необработанная ошибка на %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Внутренняя ошибка сервера"},
        )


__all__ = ["ConflictError", "register_exception_handlers"]
