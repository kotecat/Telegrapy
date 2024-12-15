import logging

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse

from src.api.routes import api, frontend
from src.config import app_config
from src.repository.database import async_db
from src.models.entities import Base


logging.basicConfig(level=app_config.LOGGING_LEVEL)
logger = logging.getLogger(__name__)


async def on_startup() -> None:
    async with async_db.async_engine.begin() as conn:
        ...


def init_application() -> FastAPI:
    app = FastAPI(
        debug=app_config.APP_DEBUG,
        title=app_config.TITLE,
        description=app_config.TITLE,
        docs_url='/docs' if app_config.API_DOCS else None,
        redoc_url='/redoc' if app_config.API_DOCS else None,
        on_startup=[on_startup]
    )
    
    app.include_router(api.router)
    
    if (app_config.FRONTEND_ENABLED):
        app.include_router(frontend.router)
        app.mount("/static", frontend.static_router)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=app_config.ALLOWED_ORIGINS.split(","),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
        return JSONResponse(
            content={
                "detail": f"Too Many Requests. Please try again later.",
                "limit": str(exc.detail)
            },
            status_code=429,
        )
    
    return app


telegrapy_app: FastAPI = init_application()


if __name__ == "__main__": 
    uvicorn.run(
        "main:telegrapy_app",
        host=app_config.SERVER_HOST,
        port=app_config.SERVER_PORT,
        reload=app_config.APP_DEBUG,
        workers=app_config.SERVER_WORKERS,
        log_level=app_config.LOGGING_LEVEL
    )
