import asyncio
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


async def retry_async(
    func: Callable[[], Awaitable[T]],
    attempts: int,
    base_delay: float = 0.5,
    retry_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> T:
    last_exc: Exception | None = None
    for i in range(1, attempts + 1):
        try:
            return await func()
        except retry_exceptions as exc:
            last_exc = exc
            if i == attempts:
                break
            await asyncio.sleep(base_delay * i)
    if last_exc is not None:
        raise last_exc
    raise RuntimeError("retry_async failed without exception")
