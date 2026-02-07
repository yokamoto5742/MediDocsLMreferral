from fastapi import APIRouter, Depends

from app.api import evaluation, prompts, settings, statistics, summary
from app.core.security import require_csrf_token

# 管理用ルーター（Web UIから使用）
admin_router = APIRouter()
admin_router.include_router(prompts.router)
admin_router.include_router(settings.router)
admin_router.include_router(statistics.router)
admin_router.include_router(summary.router)  # /models エンドポイント
admin_router.include_router(evaluation.router)  # 評価プロンプト管理エンドポイント

# 保護されたAPIルーター（認証必須）
protected_api_router = APIRouter(dependencies=[Depends(require_csrf_token)])
protected_api_router.include_router(summary.protected_router)  # /generate エンドポイント
protected_api_router.include_router(evaluation.protected_router)  # /evaluate エンドポイント

# 統合ルーター
api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(protected_api_router)
