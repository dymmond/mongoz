from contextlib import asynccontextmanager
from typing import AsyncIterator, Protocol, TypeVar


class AsyncClosableCursor(Protocol):
    async def close(self) -> None: ...


CursorT = TypeVar("CursorT", bound=AsyncClosableCursor)


@asynccontextmanager
async def closing_cursor(cursor: CursorT) -> AsyncIterator[CursorT]:
    """Close a cursor without replacing an in-flight operation failure."""
    try:
        yield cursor
    except GeneratorExit:
        await cursor.close()
        raise
    except BaseException as operation_error:
        try:
            await cursor.close()
        except BaseException as cleanup_error:
            raise operation_error from cleanup_error
        raise
    else:
        await cursor.close()
