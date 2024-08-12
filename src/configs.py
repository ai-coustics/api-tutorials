from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    api_key: str


def get_configs() -> Configs:
    return Configs()
