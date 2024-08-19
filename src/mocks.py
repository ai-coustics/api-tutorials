import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path


@asynccontextmanager
async def mock_get_media_queue(
    source_folder: Path = Path("samples"),
    n_tasks: int | None = None,
    period: float = 5.0,
) -> AsyncGenerator[asyncio.Queue[Path]]:
    queue = asyncio.Queue()

    async def produce(file_path: Path) -> None:
        while True:
            await queue.put(file_path)
            await asyncio.sleep(period)

    files = [file_path for file_path in source_folder.rglob("*") if file_path.is_file()]
    if n_tasks is None:
        n_tasks = len(files)
    if len(files) < n_tasks:
        raise ValueError(
            f"Requested n_tasks '{n_tasks}' is bigger than"
            f"number of files '{len(files)}' in the source_folder {str(source_folder)}"
        )

    tasks: list[asyncio.Task] = []
    for i in range(n_tasks):
        file_path = files[i]
        task = asyncio.create_task(produce(file_path))
        tasks.append(task)

    yield queue

    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks)
