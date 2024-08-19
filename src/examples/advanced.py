import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Self

import aiofiles
import aiohttp
from aiofiles import os as aiofiles_os
from fastapi import FastAPI, Header, HTTPException, status
from pydantic import BaseModel
from uvicorn import Config as UvicornConfig
from uvicorn import Server

from src.configs import Configs, get_configs
from src.mocks import mock_get_media_queue

# API_URL = "https://api.ai-coustics.com/v1"
API_URL = "http://localhost:8000/v1"
CHUNK_SIZE = 2048


class EnhancementParamsTO(BaseModel):
    loudness_target_level: int = -14
    loudness_peak_limit: int = -1
    enhancement_level: float = 1.0
    transcode_kind: str


class EnhancedMediaCallbackTO(BaseModel):
    generated_name: str


class MediaEnhancementClient:
    def __init__(
        self: Self,
        incoming_media_queue: asyncio.Queue[Path],
        enhancement_params: EnhancementParamsTO,
        result_media_file_extension: str,
        output_folder: Path,
        webhook_server_host: str,
        webhook_server_port: int,
        upload_tasks_n: int = 50,
        download_tasks_n: int = 50,
        http_connections_limit: int = 100,
        http_request_timeout: int = 300.0,
        shutdown_timeout: float = 60.0,
    ) -> None:
        self.incoming_media_queue = incoming_media_queue
        self.enhanced_media_queue: asyncio.Queue[str] = asyncio.Queue()
        self.result_media_queue: asyncio.Queue[Path] = asyncio.Queue()

        self.enhancement_params = enhancement_params
        self.result_media_file_extension = result_media_file_extension
        self.output_folder = output_folder

        self.webhook_server_host = webhook_server_host
        self.webhook_server_port = webhook_server_port

        self.upload_tasks_n = upload_tasks_n
        self.download_tasks_n = download_tasks_n

        self.http_connections_limit = http_connections_limit
        self.http_request_timeout = http_request_timeout
        self.shutdown_timeout = shutdown_timeout

        self._configs: Configs = get_configs()
        self._http_session: aiohttp.ClientSession

    @asynccontextmanager
    async def _open_http_session(self: Self) -> AsyncGenerator[None]:
        connector = aiohttp.TCPConnector(limit=self.http_connections_limit)
        timeout = aiohttp.ClientTimeout(total=self.http_request_timeout)
        headers = {"X-API-Key": self._configs.api_key}

        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=timeout,
        ) as _http_session:
            self._http_session = _http_session
            yield

    async def upload(self: Self, file_path: Path) -> str | None:
        url = f"{API_URL}/media/enhance"

        form_data = aiohttp.FormData()
        for field_name, field_value in self.enhancement_params:
            form_data.add_field(field_name, str(field_value))

        async with aiofiles.open(file_path, "rb") as file:
            form_data.add_field(
                "file",
                file,
                content_type="application/octet-stream",
                filename=file_path.name,
            )

            async with self._http_session.post(url, data=form_data) as response:
                if response.status != status.HTTP_201_CREATED:
                    response_text = await response.text()
                    print(f"Error occured: {response_text}")
                    return None

                response_json = await response.json()
                return response_json["generated_name"]

    async def download(
        self: Self,
        generated_name: str,
        file_extension: str,
    ) -> Path | None:
        url = f"{API_URL}/media/{generated_name}"
        file_name = f"{generated_name}.{file_extension}"
        output_file_path = self.output_folder / file_name

        async with self._http_session.get(url) as response:
            if response.status != status.HTTP_200_OK:
                response_text = await response.text()
                print(f"Error occured: {response_text}")
                return None

            await aiofiles_os.makedirs(output_file_path.parent, exist_ok=True)
            async with aiofiles.open(output_file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    await f.write(chunk)

        return output_file_path

    async def _process_callbacks(self: Self) -> None:
        app = FastAPI()

        @app.post("/callbacks")
        async def handle_callbacks(
            data: EnhancedMediaCallbackTO,
            x_signature: str = Header(...),
        ) -> None:
            if (
                self._configs.callback_signature is not None
                and x_signature != self._configs.callback_signature
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature",
                )

            await self.enhanced_media_queue.put(data.generated_name)

        config = UvicornConfig(
            app,
            host=self.webhook_server_host,
            port=self.webhook_server_port,
        )
        server = Server(config)
        await server.serve()

    async def _process_incoming(self: Self) -> None:
        async def _process() -> None:
            while True:
                file_path = await self.incoming_media_queue.get()
                await self.upload(file_path)

        tasks: list[asyncio.Task] = []
        for _ in self.upload_tasks_n:
            task = asyncio.create_task(_process())
            tasks.append(task)
        await asyncio.gather(*tasks)

    async def _process_enhanced(self: Self) -> None:
        async def _process(generated_name: str) -> None:
            generated_name = await self.enhanced_media_queue.get()
            file_path = await self.download(
                generated_name,
                self.result_media_file_extension,
            )
            if file_path is not None:
                await self.result_media_queue.put(file_path)

        tasks: list[asyncio.Task] = []
        for _ in self.download_tasks_n:
            task = asyncio.create_task(_process())
            tasks.append(task)
        await asyncio.gather(*tasks)

    @asynccontextmanager
    async def run(self: Self) -> AsyncGenerator[asyncio.Queue[Path]]:
        tasks: list[asyncio.Task] = []

        try:
            async with self._open_http_session():
                tasks = (
                    asyncio.create_task(self._process_incoming()),
                    asyncio.create_task(self._process_enhanced()),
                    asyncio.create_task(self._process_callbacks()),
                )
                yield self.result_media_queue
        except asyncio.CancelledError:
            pass
        finally:
            for task in tasks:
                task.cancel()
            await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                self.shutdown_timeout,
            )


async def main() -> None:
    transcode_kind, result_media_file_extension = "WAV", "wav"
    enhancement_params = EnhancementParamsTO(transcode_kind=transcode_kind)
    output_folder = Path("results")

    async with mock_get_media_queue() as incoming_media_queue:
        client = MediaEnhancementClient(
            incoming_media_queue=incoming_media_queue,
            enhancement_params=enhancement_params,
            result_media_file_extension=result_media_file_extension,
            output_folder=output_folder,
            tasks_limit=100,
            http_connections_limit=100,
            http_request_timeout=60.0,
        )
        async with client.run() as processed_media_queue:
            pass


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    main_task = loop.create_task(main())

    try:
        loop.run_until_complete(main_task)
    except KeyboardInterrupt:
        main_task.cancel()
        loop.run_until_complete(main_task)
    finally:
        loop.close()
