"""Runtime settings, read from environment variables at call time (never hardcoded secrets)."""
import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR.parent / "frontend"


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    data_path: Path
    llm_api_key: str
    llm_model: str
    live_fetch: bool
    stale_days: int
    rate_limit_per_minute: int
    max_upload_bytes: int


def get_settings() -> Settings:
    data_path = os.getenv("CIVICLENS_DATA_PATH") or str(BASE_DIR / "data" / "schemes.json")
    return Settings(
        data_path=Path(data_path),
        llm_api_key=os.getenv("ANTHROPIC_API_KEY", ""),
        llm_model=os.getenv("CIVICLENS_LLM_MODEL") or "claude-sonnet-5-5",
        live_fetch=os.getenv("CIVICLENS_LIVE_FETCH", "0") == "1",
        stale_days=_int("CIVICLENS_STALE_DAYS", 90),
        rate_limit_per_minute=_int("CIVICLENS_RATE_LIMIT_PER_MINUTE", 120),
        max_upload_bytes=_int("CIVICLENS_MAX_UPLOAD_BYTES", 2_000_000),
    )


def today() -> date:
    raw = os.getenv("CIVICLENS_TODAY", "").strip()
    if raw:
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    return date.today()
