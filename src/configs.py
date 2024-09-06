from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    api_key: str
    callback_signature: str | None = None


def get_configs() -> Configs:
    return Configs()
