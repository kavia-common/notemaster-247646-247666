import os
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    postgres_url: str
    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int
    cors_allow_origins: List[str]


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            "Set it in the container .env file."
        )
    return value


def _parse_csv(value: str) -> List[str]:
    return [v.strip() for v in value.split(",") if v.strip()]


# PUBLIC_INTERFACE
def get_settings() -> Settings:
    """Load Settings from environment variables."""
    cors_raw = os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000")
    return Settings(
        postgres_url=_get_required_env("POSTGRES_URL"),
        jwt_secret_key=_get_required_env("JWT_SECRET_KEY"),
        jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
        access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080")),
        cors_allow_origins=_parse_csv(cors_raw),
    )
