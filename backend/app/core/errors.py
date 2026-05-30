"""
Базовые классы исключений приложения.

Исключения содержат HTTP-статус и код ошибки.
FastAPI-обработчики преобразуют их в Error/ValidationError JSON из OpenAPI-контракта.
"""


class AppError(Exception):
    """Базовое исключение приложения.

    Attributes:
        status_code: HTTP-статус ответа.
        code: Машинный код ошибки (например, "not_found", "conflict").
        message: Человекочитаемое описание ошибки.
        details: Дополнительные данные об ошибке (опционально).
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class UnauthorizedError(AppError):
    """Ошибка аутентификации — неверные учётные данные или отсутствует токен."""

    def __init__(self, message: str = "Неверные учётные данные или отсутствует токен") -> None:
        super().__init__(status_code=401, code="unauthorized", message=message)


class NotFoundError(AppError):
    """Запрошенный ресурс не найден."""

    def __init__(self, message: str = "Ресурс не найден") -> None:
        super().__init__(status_code=404, code="not_found", message=message)


class ConflictError(AppError):
    """Конфликт данных — дубликат, нарушение уникальности или бизнес-ограничений."""

    def __init__(self, message: str = "Конфликт данных") -> None:
        super().__init__(status_code=409, code="conflict", message=message)


class ValidationError(AppError):
    """Ошибка валидации входных данных."""

    def __init__(self, message: str = "Ошибка валидации", details: dict | None = None) -> None:
        super().__init__(status_code=422, code="validation_error", message=message, details=details)


class ForbiddenError(AppError):
    """Доступ запрещён — у пользователя нет прав на операцию."""

    def __init__(self, message: str = "Доступ запрещён") -> None:
        super().__init__(status_code=403, code="forbidden", message=message)
