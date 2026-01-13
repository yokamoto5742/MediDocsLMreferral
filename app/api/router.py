from fastapi import APIRouter

from app.api import summary, prompts, statistics, settings

api_router = APIRouter()
api_router.include_router(summary.router)
api_router.include_router(prompts.router)
api_router.include_router(statistics.router)
api_router.include_router(settings.router)
