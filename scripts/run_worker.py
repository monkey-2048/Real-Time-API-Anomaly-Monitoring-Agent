import asyncio

from app.workers.worker import run_worker_forever


if __name__ == "__main__":
    asyncio.run(run_worker_forever())
