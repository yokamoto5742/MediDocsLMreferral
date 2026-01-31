from fastapi import APIRouter, Depends

from app.api import evaluation, prompts, settings, statistics, summary
from app.core.security import verify_api_key

# 管理用ルーター（認証不要） - Web UIからアクセスされる内部管理機能
admin_router = APIRouter()
admin_router.include_router(prompts.router)
admin_router.include_router(settings.router)
admin_router.include_router(statistics.router)
admin_router.include_router(summary.router)  # /models エンドポイントのみ
admin_router.include_router(evaluation.router)  # プロンプト管理エンドポイント

# 公開APIルーター（認証必須） - 外部からアクセスされる可能性のある機能
public_api_router = APIRouter(dependencies=[Depends(verify_api_key)])
public_api_router.include_router(summary.protected_router)  # /generate エンドポイント
public_api_router.include_router(evaluation.protected_router)  # /evaluate エンドポイント

# 統合ルーター
api_router = APIRouter()
api_router.include_router(admin_router)
api_router.include_router(public_api_router)
