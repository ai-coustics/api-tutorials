import asyncio
from pathlib import Path
from typing import Any

import aiohttp

API_URL = "https://api.ai-coustics.com/v1"
API_KEY = "your_api_key"


async def upload_and_enhance(
    url: str,
    file_path: Path,
    arguments: dict[str, Any],
) -> str:
    form_data = aiohttp.FormData()
    for field_name, field_value in arguments.items():
        form_data.add_field(field_name, str(field_value))

    with open(file_path, "rb") as file:
        form_data.add_field(
            "file",
            file,
            content_type="application/octet-stream",
            filename=file_path.name,
        )

        async with aiohttp.ClientSession(headers={"X-API-Key": API_KEY}) as session:
            async with session.post(url, data=form_data) as response:
                response_json = await response.json()
                return response_json["generated_name"]


def main() -> None:
    url = f"{API_URL}/media/enhance"
    file_path = Path("samples/sample.mp3")
    arguments = {
        "loudness_target_level": -14,
        "loudness_peak_limit": -1,
        "enhancement_level": 1.0,
        "transcode_kind": "MP3",
    }

    generated_name = asyncio.run(
        upload_and_enhance(
            url,
            file_path,
            arguments,
        )
    )
    print(f"Uploaded file's generated name: {generated_name}")


if __name__ == "__main__":
    main()
