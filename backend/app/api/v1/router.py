from fastapi import APIRouter

from app.api.v1.routes import assessments, health, locations

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assessments.router, tags=["assessments"])
api_router.include_router(locations.router, tags=["locations"])
