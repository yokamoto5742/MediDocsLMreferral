from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError


async def api_exception_handler(request: Request, exc: Exception):
    """API例外ハンドラ"""
    return JSONResponse(
        status_code=500,
        content={"success": False, "error_message": str(exc)},
    )


async def validation_exception_handler(request: Request, exc: ValidationError):
    """バリデーションエラーハンドラ"""
    return JSONResponse(
        status_code=422,
        content={"success": False, "error_message": str(exc)},
    )
