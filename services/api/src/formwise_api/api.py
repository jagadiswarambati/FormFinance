import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from formwise_api.assignments.router import router as assignments_router
from formwise_api.authentication.models import AuthenticatedIdentity, CurrentUserResponse
from formwise_api.authentication.repository import UserRepository
from formwise_api.config import Settings, get_settings
from formwise_api.conversations.router import router as conversations_router
from formwise_api.dependencies.authentication import (
    get_authenticated_identity,
    get_user_repository,
)
from formwise_api.documents.router import router as documents_router
from formwise_api.readiness import readiness_report
from formwise_api.rendering.router import router as rendering_router
from formwise_api.settlements.router import router as settlements_router

router = APIRouter()
logger = structlog.get_logger()
router.include_router(documents_router)
router.include_router(conversations_router)
router.include_router(assignments_router)
router.include_router(rendering_router)
router.include_router(settlements_router)

@router.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", tags=["system"])
async def ready(settings: Settings = Depends(get_settings)) -> JSONResponse:
    is_ready, report = await readiness_report(settings)
    if not is_ready:
        logger.error(
            "dependency_unavailable",
            dependency="readiness",
            error_type="ReadinessCheckFailed",
            error_message="One or more required readiness checks failed.",
            readiness_dependencies=report["dependencies"],
        )
    return JSONResponse(status_code=200 if is_ready else 503, content=report)


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    response_model_by_alias=True,
    tags=["authentication"],
)
async def current_user(
    identity: AuthenticatedIdentity = Depends(get_authenticated_identity),
    repository: UserRepository = Depends(get_user_repository),
) -> CurrentUserResponse:
    return repository.upsert_on_login(identity)
