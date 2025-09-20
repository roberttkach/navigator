import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    history_limit: int = Field(18, ge=1, le=200)
    chunk: int = Field(100, ge=1, le=100)
    truncate: bool = Field(False)  # управляемое усечение текста/подписи; ENV: NAV_TRUNCATE in {1,true,yes}


SETTINGS = Settings(
    history_limit=int(os.getenv("NAV_HISTORY_LIMIT", "18")),
    chunk=int(os.getenv("NAV_CHUNK", "100")),
    truncate=os.getenv("NAV_TRUNCATE", "0").lower() in {"1", "true", "yes"},
)
