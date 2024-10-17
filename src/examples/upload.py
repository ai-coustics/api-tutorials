import asyncio
from pathlib import Path
from typing import Any

import aiofiles
import aiohttp

from src.configs import get_configs

configs = get_configs()

API_URL = "https://api.ai-coustics.com/v1"


async def upload_and_enhance(
    url: str,
    file_path: Path,
    arguments: dict[str, Any],
) -> str:
    form_data = aiohttp.FormData()
    for field_name, field_value in arguments.items():
        form_data.add_field(field_name, str(field_value))

    async with aiofiles.open(file_path, "rb") as file:
        form_data.add_field(
            "file",
            file,
            content_type="application/octet-stream",
            filename=file_path.name,
        )

        async with aiohttp.ClientSession(
            headers={"X-API-Key": configs.api_key}
        ) as session:
            async with session.post(url, data=form_data) as response:
                if response.status != 201:
                    response_text = await response.text()
                    print(f"Error occured: {response_text}")
                    return None

                response_json = await response.json()
                generated_name = response_json["generated_name"]
                print(f"Uploaded file's generated name: {generated_name}")
                return generated_name


def main(file_path: Path, arguments: dict[str, Any]) -> None:
    url = f"{API_URL}/media/enhance"

    asyncio.run(
        upload_and_enhance(
            url,
            file_path,
            arguments,
        )
    )


if __name__ == "__main__":
    file_path = Path("samples/sample.mp3")
    arguments = {
        "loudness_target_level": -14,
        "loudness_peak_limit": -1,
        "enhancement_level": 1.0,
        "transcode_kind": "MP3",
    }
    main(file_path, arguments)
