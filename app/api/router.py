from fastapi import APIRouter

from app.api import evaluation, prompts, settings, statistics, summary

api_router = APIRouter()
api_router.include_router(evaluation.router)
api_router.include_router(prompts.router)
api_router.include_router(settings.router)
api_router.include_router(statistics.router)
api_router.include_router(summary.router)
