from fastapi import APIRouter
from app.api.v1.routes import health, auth, project, chat, review # <-- NEW

api_router = APIRouter()

api_router.include_router(
    health.router,
    tags=["Health"]
)

api_router.include_router(
    auth.router
)

api_router.include_router(
    project.router
)

api_router.include_router(
    chat.router
)

api_router.include_router(
    review.router # <-- NEW
)