from fastapi import APIRouter, Depends

from app.api import evaluation, prompts, settings, statistics, summary
from app.core.security import verify_api_key

api_router = APIRouter(dependencies=[Depends(verify_api_key)])
api_router.include_router(evaluation.router)
api_router.include_router(prompts.router)
api_router.include_router(settings.router)
api_router.include_router(statistics.router)
api_router.include_router(summary.router)
