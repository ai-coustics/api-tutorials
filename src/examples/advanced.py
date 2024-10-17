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
from src.mocks import mock_get_media_queue, mock_process_enhanced_media

API_URL = "https://api.ai-coustics.com/v1"
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
        http_request_timeout: int = 30.0,
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
        self._background_tasks: list[asyncio.Task] = []

    @staticmethod
    def task_done_callback(task: asyncio.Task) -> None:
        try:
            task.result()
        except Exception as e:
            print(f"Task raised an exception: {e}")

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

    async def _start_process_callbacks(self: Self) -> None:
        app = FastAPI()
        config = UvicornConfig(
            app,
            host=self.webhook_server_host,
            port=self.webhook_server_port,
        )
        server = Server(config)

        @app.post("/callbacks")
        async def handle_callbacks(
            data: EnhancedMediaCallbackTO,
            x_signature: str = Header(...),
        ) -> None:
            if (
                self._configs.webhook_signature is not None
                and x_signature != self._configs.webhook_signature
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid signature",
                )

            await self.enhanced_media_queue.put(data.generated_name)

        task = asyncio.create_task(server.serve())
        self._background_tasks.append(task)
        task.add_done_callback(self.task_done_callback)

    async def _start_process_incoming(self: Self) -> None:
        async def _process() -> None:
            while True:
                file_path = await self.incoming_media_queue.get()
                await self.upload(file_path)

        for _ in range(self.upload_tasks_n):
            task = asyncio.create_task(_process())
            self._background_tasks.append(task)
            task.add_done_callback(self.task_done_callback)

    async def _start_process_enhanced(self: Self) -> None:
        async def _process() -> None:
            generated_name = await self.enhanced_media_queue.get()
            file_path = await self.download(
                generated_name,
                self.result_media_file_extension,
            )
            if file_path is not None:
                await self.result_media_queue.put(file_path)

        for _ in range(self.download_tasks_n):
            task = asyncio.create_task(_process())
            self._background_tasks.append(task)
            task.add_done_callback(self.task_done_callback)

    @asynccontextmanager
    async def run(self: Self) -> AsyncGenerator[asyncio.Queue[Path]]:
        async with self._open_http_session():
            await self._start_process_incoming()
            await self._start_process_enhanced()
            await self._start_process_callbacks()

            yield self.result_media_queue


async def main(
    transcode_kind: str,
    result_media_file_extension: str,
    webhook_server_host: str,
    webhook_server_port: int,
    mock_get_media_queue_period: float,
) -> None:
    enhancement_params = EnhancementParamsTO(transcode_kind=transcode_kind)
    output_folder = Path("results")

    async with mock_get_media_queue(
        period=mock_get_media_queue_period
    ) as incoming_media_queue:
        client = MediaEnhancementClient(
            incoming_media_queue,
            enhancement_params,
            result_media_file_extension,
            output_folder,
            webhook_server_host,
            webhook_server_port,
        )
        async with client.run() as enhanced_media_queue:
            await mock_process_enhanced_media(enhanced_media_queue)


if __name__ == "__main__":
    transcode_kind, result_media_file_extension = "WAV", "wav"
    webhook_server_host = "localhost"
    webhook_server_port = 8002
    mock_get_media_queue_period = 60.0

    asyncio.run(
        main(
            transcode_kind,
            result_media_file_extension,
            webhook_server_host,
            webhook_server_port,
            mock_get_media_queue_period,
        )
    )
