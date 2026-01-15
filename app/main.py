from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pydantic import ValidationError

from app.api.router import api_router
from app.core.config import get_settings
from app.core.constants import DEFAULT_DEPARTMENT, DOCUMENT_TYPES, TAB_NAMES
from app.utils.error_handlers import api_exception_handler, validation_exception_handler

settings = get_settings()

app = FastAPI(
    title="MediDocs API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# エラーハンドラーを登録
app.add_exception_handler(ValidationError, validation_exception_handler)
app.add_exception_handler(Exception, api_exception_handler)

# 静的ファイル
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# テンプレート
templates = Jinja2Templates(directory="app/templates")

# API ルーター
app.include_router(api_router, prefix="/api")


def get_available_models() -> list[str]:
    """利用可能なモデル一覧を取得"""
    models = []
    if settings.anthropic_model or settings.claude_api_key:
        models.append("Claude")
    if settings.gemini_model:
        models.append("Gemini_Pro")
    return models if models else ["Claude"]


def get_common_context(active_page: str = "index") -> dict:
    """共通コンテキストを取得"""
    return {
        "departments": DEFAULT_DEPARTMENT,
        "document_types": DOCUMENT_TYPES,
        "available_models": get_available_models(),
        "tab_names": TAB_NAMES,
        "active_page": active_page,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """メインページ"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, **get_common_context()},
    )


@app.get("/prompts", response_class=HTMLResponse)
async def prompts_page(request: Request):
    """プロンプト管理ページ"""
    return templates.TemplateResponse(
        "prompts.html",
        {"request": request, **get_common_context("prompts")},
    )


@app.get("/statistics", response_class=HTMLResponse)
async def statistics_page(request: Request):
    """統計ページ"""
    return templates.TemplateResponse(
        "statistics.html",
        {"request": request, **get_common_context("statistics")},
    )


@app.get("/health")
async def health_check():
    """ヘルスチェックエンドポイント"""
    return {"status": "healthy"}
