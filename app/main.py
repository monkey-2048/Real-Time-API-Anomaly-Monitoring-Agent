from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.scheduler.scheduler import ProducerScheduler
from app.services.queue import RedisQueue

settings = get_settings()
BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    configure_logging()
    init_db()

    # Initialize the Redis queue and scheduler runner, and store them in the application state for later use.
    app.state.queue = RedisQueue()
    app.state.scheduler_runner = None

    if settings.run_scheduler_in_api:
        runner = ProducerScheduler()
        runner.start()
        app.state.scheduler_runner = runner

    yield

    if app.state.scheduler_runner is not None:
        await app.state.scheduler_runner.stop()
    await app.state.queue.close()


# Create the FastAPI application instance, including the lifespan context manager and API routes.
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
app.include_router(router)
