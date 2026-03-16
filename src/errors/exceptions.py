class AppError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: str,
        message: str,
        context: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.context = context or {}


class BadRequestError(AppError):
    def __init__(self, message: str, code: str = "BAD_REQUEST", context: dict | None = None) -> None:
        super().__init__(status_code=400, code=code, message=message, context=context)


class NotFoundError(AppError):
    def __init__(self, message: str, code: str = "NOT_FOUND", context: dict | None = None) -> None:
        super().__init__(status_code=404, code=code, message=message, context=context)


class ConflictError(AppError):
    def __init__(self, message: str, code: str = "CONFLICT", context: dict | None = None) -> None:
        super().__init__(status_code=409, code=code, message=message, context=context)


class StorageError(AppError):
    def __init__(self, message: str, code: str = "STORAGE_ERROR", context: dict | None = None) -> None:
        super().__init__(status_code=500, code=code, message=message, context=context)
