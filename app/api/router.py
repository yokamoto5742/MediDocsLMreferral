from fastapi import APIRouter, Depends

from app.api import evaluation, prompts, settings, statistics, summary
from app.core.security import verify_api_key

# 認証が必要なルーター
authenticated_router = APIRouter(dependencies=[Depends(verify_api_key)])
authenticated_router.include_router(evaluation.router)
authenticated_router.include_router(prompts.router)
authenticated_router.include_router(statistics.router)
authenticated_router.include_router(summary.router)

# メインAPIルーター
api_router = APIRouter()
api_router.include_router(authenticated_router)
api_router.include_router(settings.router)  # 認証不要
