from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from formwise_api.api import router
from formwise_api.config import get_settings
from formwise_api.errors import register_exception_handlers
from formwise_api.logging import configure_logging
from formwise_api.middleware import ApiSecurityMiddleware


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    configure_logging(get_settings().log_level)
    yield


settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_allowed_origins),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=list(settings.cors_allowed_methods),
    allow_headers=list(settings.cors_allowed_headers),
    expose_headers=list(settings.cors_expose_headers),
    max_age=settings.cors_max_age_seconds,
)
app.add_middleware(ApiSecurityMiddleware, settings=settings)

app.include_router(router, prefix=settings.api_prefix)
register_exception_handlers(app)
