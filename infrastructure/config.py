import os

from pydantic import BaseModel, Field


class Settings(BaseModel):
    history_limit: int = Field(18, ge=1, le=200)
    chunk: int = Field(100, ge=1, le=100)
    truncate: bool = Field(False)  # управляемое усечение текста/подписи; ENV: NAV_TRUNCATE in {1,true,yes}
    strict_inline_media_path: bool = Field(True)  # ENV: NAV_STRICT_INLINE_MEDIA_PATH in {1,true,yes}
    detect_thumb_change: bool = Field(False)
    log_redaction_mode: str = Field("safe")


SETTINGS = Settings(
    history_limit=int(os.getenv("NAV_HISTORY_LIMIT", "18")),
    chunk=int(os.getenv("NAV_CHUNK", "100")),
    truncate=os.getenv("NAV_TRUNCATE", "0").lower() in {"1", "true", "yes"},
    strict_inline_media_path=os.getenv("NAV_STRICT_INLINE_MEDIA_PATH", "1").lower() in {"1", "true", "yes"},
    detect_thumb_change=os.getenv("NAV_DETECT_THUMB_CHANGE", "0").lower() in {"1", "true", "yes"},
    log_redaction_mode=os.getenv("NAV_LOG_REDACTION", "safe").lower(),
)
