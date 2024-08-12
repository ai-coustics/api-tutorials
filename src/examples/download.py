import asyncio
from pathlib import Path

import aiofiles
import aiohttp
from aiofiles import os

API_URL = "https://api.ai-coustics.com/v1"
API_KEY = "your_api_key"

CHUNK_SIZE = 1024


async def download_enhanced_media(
    url: str,
    output_file_path: Path,
) -> None:
    async with aiohttp.ClientSession(headers={"X-API-Key": API_KEY}) as session:
        async with session.get(url) as response:
            response.raise_for_status()

            await os.makedirs(output_file_path.parent, exist_ok=True)
            async with aiofiles.open(output_file_path, "wb") as f:
                async for chunk in response.content.iter_chunked(CHUNK_SIZE):
                    await f.write(chunk)


def main(generated_name: str, expected_media_format: str) -> None:
    url = f"{API_URL}/media/{generated_name}"
    output_file_path = Path("results", f"{generated_name}.{expected_media_format}")

    asyncio.run(
        download_enhanced_media(
            url,
            output_file_path,
        )
    )
    print(f"Download successfully to: {output_file_path}")


if __name__ == "__main__":
    generated_name = "f0e6c12c7be4459a802710ad109b4815"
    expected_media_format = "mp3"
    main(generated_name, expected_media_format)
