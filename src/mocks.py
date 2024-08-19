import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path


async def mock_get_media_queue() -> AsyncGenerator[asyncio.Queue[Path]]:
    queue = asyncio.Queue()

    source_folder = Path("samples")
    files = [file_path for file_path in source_folder.rglob("*") if file_path.is_file()]

    async def produce(n: int) -> None:
        while True:
            await queue.put(files[n])
            await asyncio.sleep(5)

    tasks = [asyncio.create_task(produce(0)), asyncio.create_task(produce(1))]
    yield queue

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks)
