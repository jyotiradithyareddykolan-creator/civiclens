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
    llm_provider: str = "anthropic"


def _llm_choice() -> tuple[str, str, str]:
    """(provider, key, default_model). CIVICLENS_LLM_PROVIDER = anthropic | gemini. If unset, use whichever key exists
    (Anthropic first). Keys are read only here, only server-side."""
    a, g = os.getenv("ANTHROPIC_API_KEY", ""), os.getenv("GEMINI_API_KEY", "")
    provider = os.getenv("CIVICLENS_LLM_PROVIDER", "").strip().lower()
    if provider not in ("anthropic", "gemini"):
        provider = "gemini" if (g and not a) else "anthropic"
    if provider == "gemini":
        return "gemini", g, "gemini-2.5-flash"
    return "anthropic", a, "claude-sonnet-5-5"


def get_settings() -> Settings:
    provider, key, default_model = _llm_choice()
    data_path = os.getenv("CIVICLENS_DATA_PATH") or str(BASE_DIR / "data" / "schemes.json")
    return Settings(
        data_path=Path(data_path),
        llm_api_key=key,
        llm_model=os.getenv("CIVICLENS_LLM_MODEL") or default_model,
        llm_provider=provider,
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
