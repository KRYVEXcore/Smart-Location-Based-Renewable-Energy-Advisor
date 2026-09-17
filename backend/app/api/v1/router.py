from fastapi import APIRouter

from app.api.v1.routes import assessments, health, incentives, locations, solar, tariffs

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(assessments.router, tags=["assessments"])
api_router.include_router(locations.router, tags=["locations"])
api_router.include_router(solar.router, tags=["solar"])
api_router.include_router(tariffs.router, tags=["tariffs"])
api_router.include_router(incentives.router, tags=["incentives"])
