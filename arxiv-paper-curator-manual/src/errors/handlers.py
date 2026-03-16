import json

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.errors.exceptions import AppError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):  # type: ignore[unused-ignore]
        payload = {
            "error_code": exc.code,
            "message": exc.message,
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
            "context": exc.context,
        }
        print(f"[error] {json.dumps(payload, sort_keys=True)}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "error": {
                    "code": exc.code,
                    "message": exc.message,
                    "context": exc.context,
                },
            },
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):  # type: ignore[unused-ignore]
        payload = {
            "error_code": "INTERNAL_ERROR",
            "message": str(exc),
            "status_code": 500,
            "path": request.url.path,
            "method": request.method,
        }
        print(f"[error] {json.dumps(payload, sort_keys=True)}")
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Internal server error",
                    "context": {},
                },
            },
        )
