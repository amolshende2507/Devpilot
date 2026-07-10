from fastapi import APIRouter

from app.api.v1.routes import health
from app.api.v1.routes import auth

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    auth.router
)