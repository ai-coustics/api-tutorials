from pydantic_settings import BaseSettings


class Configs(BaseSettings):
    """A `Pydantic BaseSettings` model for application configuration.

    Attributes:
        api_key (str): An ai|coustics API key that you can get on our
            [developer portal](https://developers.ai-coustics.com/signup).
        webhook_signature (str | None): An optional signature that you set for a webhook
            on our [developer portal](https://developers.ai-coustics.com/signup). It is
            used in the `src/exaples/advanced.py` example file for verifying incomming
            webhook requests.
    """

    api_key: str
    webhook_signature: str | None = None


def get_configs() -> Configs:
    return Configs()
