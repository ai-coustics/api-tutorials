import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Self

import aiofiles
import aiohttp
from aiofiles import os as aiofiles_os
from fastapi import status
from pydantic import BaseModel

from src.configs import Configs, get_configs

# API_URL = "https://api.ai-coustics.com/v1"
API_URL = "http://localhost:8000/v1"
CHUNK_SIZE = 2048


class EnhancementParams(BaseModel):
    loudness_target_level: int = -14
    loudness_peak_limit: int = -1
    enhancement_level: float = 1.0
    transcode_kind: str


class MediaEnhancementClient:
    def __init__(
        self: Self,
        enhancement_params: EnhancementParams,
        output_folder: Path,
        http_connections_limit: int,
        http_request_timeout: int,
    ) -> None:
        self.enhancement_params = enhancement_params
        self.output_folder = output_folder

        self.http_connections_limit = http_connections_limit
        self.http_request_timeout = http_request_timeout

        self.configs: Configs = get_configs()
        self.http_session: aiohttp.ClientSession
        self.enhanced_media_queue: asyncio.Queue[dict] = asyncio.Queue()

    @asynccontextmanager
    async def _open_http_session(self: Self) -> AsyncGenerator[None]:
        connector = aiohttp.TCPConnector(limit=self.http_connections_limit)
        timeout = aiohttp.ClientTimeout(total=self.http_request_timeout)
        headers = {"X-API-Key": self.configs.api_key}

        async with aiohttp.ClientSession(
            connector=connector,
            headers=headers,
            timeout=timeout,
        ) as http_session:
            self.http_session = http_session
            yield

    async def upload(self: Self, file_path: Path) -> str:
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

            async with self.http_session.post(url, data=form_data) as response:
                if response.status != status.HTTP_201_CREATED:
                    response_text = await response.text()
                    print(f"Error occured: {response_text}")
                    return None

                response_json = await response.json()
                return response_json["generated_name"]

    async def download(
        self: Self,
        generated_name: str,
        expected_media_format: str,
    ) -> Path:
        url = f"{API_URL}/media/{generated_name}"
        file_name = f"{generated_name}.{expected_media_format}"
        output_file_path = self.output_folder / file_name

        async with self.http_session.get(url) as response:
            if response.status != status.HTTP_200_OK:
                response_text = await response.text()
                print(f"Error occured: {response_text}")
                return None

            await aiofiles_os.makedirs(output_file_path.parent, exist_ok=True)
            async with aiofiles.open(output_file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    await f.write(chunk)

        return output_file_path

    async def run(self: Self) -> None:
        file_path = Path("samples/sample.mp3")

        async with self._open_http_session():
            generated_name = await self.upload(file_path)
            await asyncio.sleep(10)
            await self.download(generated_name, "mp3")


if __name__ == "__main__":
    enhancement_params = EnhancementParams(transcode_kind="MP3")
    output_folder = Path("results")
    client = MediaEnhancementClient(
        enhancement_params=enhancement_params,
        output_folder=output_folder,
        http_connections_limit=100,
        http_request_timeout=60.0,
    )

    asyncio.run(client.run())
