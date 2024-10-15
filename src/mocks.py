import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path


@asynccontextmanager
async def mock_get_media_queue(
    source_folder: Path = Path("samples"),
    n_tasks: int | None = None,
    period: float = 60.0,
) -> AsyncGenerator[asyncio.Queue[Path]]:
    """Async context manager with the mock queue simulating a stream of media files.

    By changing the `n_tasks` and `period` arguments' values you can control the rate
    at what new mock media files are put into the queue. The default rate is `2` media
    files every `60.0` seconds (`2` media files since by default the `n_tasks` equals
    the number of files in the `source_folder`).

    Args:
        source_folder (Path): Source folder with media files. Defaults to
            `Path("samples")`.
        n_tasks (int | None): Optional number of `produce` tasks to be created. Defaults
            to `None`.
        period (float): Period in seconds of producing a new mock media file for each
            `produce` task. Defaults to `60.0`.

    Yields:
        asyncio.Queue[Path]]: Dynamically populated mock queue with media files' paths.
    """

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


async def mock_process_enhanced_media(queue: asyncio.Queue[Path]) -> None:
    """Mock functiong printing the results of enhanced media files."""

    while True:
        enhanced_file_path = await queue.get()
        print(f"Enhanced media file path: {enhanced_file_path}")
