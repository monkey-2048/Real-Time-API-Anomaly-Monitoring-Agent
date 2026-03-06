from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.init_db import init_db
from app.scheduler.scheduler import ProducerScheduler
from app.services.queue import RedisQueue

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    init_db()

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


app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.include_router(router)
