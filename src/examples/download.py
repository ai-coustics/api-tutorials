import asyncio
from pathlib import Path

import aiofiles
import aiohttp
from aiofiles import os as aiofiles_os

from src.configs import get_configs

configs = get_configs()

API_URL = "https://api.ai-coustics.com/v1"
CHUNK_SIZE = 1024


async def download_enhanced_media(
    url: str,
    output_file_path: Path,
) -> None:
    async with aiohttp.ClientSession(headers={"X-API-Key": configs.api_key}) as session:
        async with session.get(url) as response:
            if response.status != 200:
                response_text = await response.text()
                print(f"Error occured: {response_text}")
                return

            await aiofiles_os.makedirs(output_file_path.parent, exist_ok=True)
            async with aiofiles.open(output_file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    await f.write(chunk)

    print(f"Download successfully to: {output_file_path}")


def main(generated_name: str, expected_media_format: str) -> None:
    url = f"{API_URL}/media/{generated_name}"
    output_file_path = Path("results", f"{generated_name}.{expected_media_format}")

    asyncio.run(
        download_enhanced_media(
            url,
            output_file_path,
        )
    )


if __name__ == "__main__":
    generated_name = "generated_name_value"
    expected_media_format = "mp3"
    main(generated_name, expected_media_format)
