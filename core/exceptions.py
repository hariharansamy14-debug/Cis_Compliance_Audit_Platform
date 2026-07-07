"""
Custom application exceptions and handlers for clean JSON API error responses.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError

class AppException(Exception):
    def __init__(self, detail: str, status_code: int):
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)

class NotFoundError(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(detail, status.HTTP_404_NOT_FOUND)

class UnauthorizedError(AppException):
    def __init__(self, detail: str = "Unauthorized access"):
        super().__init__(detail, status.HTTP_401_UNAUTHORIZED)

class ForbiddenError(AppException):
    def __init__(self, detail: str = "Action forbidden"):
        super().__init__(detail, status.HTTP_403_FORBIDDEN)

class ValidationError(AppException):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(detail, status.HTTP_422_UNPROCESSABLE_ENTITY)

class ConflictError(AppException):
    def __init__(self, detail: str = "Conflict detected"):
        super().__init__(detail, status.HTTP_409_CONFLICT)

def register_exception_handlers(app: FastAPI):
    """Register custom exception handlers with the FastAPI application."""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
        
    @app.exception_handler(PydanticValidationError)
    async def pydantic_validation_exception_handler(request: Request, exc: PydanticValidationError):
        errors = exc.errors()
        error_details = [{"loc": err["loc"], "msg": err["msg"], "type": err["type"]} for err in errors]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": error_details}
        )
