import asyncio

from app.core.logging import configure_logging
from app.scheduler.scheduler import run_scheduler_forever


if __name__ == "__main__":
    configure_logging()
    asyncio.run(run_scheduler_forever())
