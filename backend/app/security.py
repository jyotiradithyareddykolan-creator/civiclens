"""Prompt-injection screening, sensitive-input rejection, upload validation, rate limiting."""
import re
import time
from collections import defaultdict, deque
from urllib.parse import urlparse

# ---------------------------------------------------------------- prompt injection
_INJECTION = {
    "ignore_instructions": r"\b(ignore|disregard|forget|override)\b.{0,40}\b(previous|prior|above|earlier|all|system)\b.{0,30}\b(instruction|prompt|rule|message)s?\b",
    "reveal_secret": r"\b(reveal|show|print|leak|output|send|expose)\b.{0,50}\b(api[\s_-]?key|secret|password|token|credential|system prompt)s?\b",
    "system_marker": r"(^|\n|\s)(system|assistant|developer)\s*:",
    "role_change": r"\b(you are now|act as|pretend to be|from now on you)\b",
    "approve_all": r"\b(approve|accept|mark)\b.{0,30}\b(every|all)\b.{0,20}\b(applicant|application|user)s?\b",
    "do_not_follow": r"\bdo not follow\b.{0,30}\b(rule|instruction|polic)",
    "tool_abuse": r"\b(call|invoke|run|execute)\b.{0,30}\b(tool|function|command|shell)\b",
}
_INJECTION_RE = {k: re.compile(v, re.IGNORECASE | re.DOTALL) for k, v in _INJECTION.items()}


def scan_text(text: str) -> list[str]:
    """Return names of injection patterns found in untrusted text."""
    return [name for name, rx in _INJECTION_RE.items() if rx.search(text or "")]


def is_suspicious(text: str) -> bool:
    return bool(scan_text(text))


def split_passages(passages: list[dict]) -> tuple[list[dict], list[dict]]:
    """Separate clean passages from instruction-like ones. Flagged text is never passed on."""
    clean, flagged = [], []
    for p in passages:
        hits = scan_text(p.get("text", "")) or scan_text(p.get("section", ""))
        if hits:
            flagged.append({**p, "flags": hits})
        else:
            clean.append(p)
    return clean, flagged


# ---------------------------------------------------------------- sensitive input
_AADHAAR = re.compile(r"(?<!\d)\d{4}[\s-]?\d{4}[\s-]?\d{4}(?!\d)")
_LONG_NUMBER = re.compile(r"(?<!\d)\d{9,18}(?!\d)")
_SECRET_WORD = re.compile(r"\b(password|passcode|otp|cvv|pin\s*number)\b", re.IGNORECASE)


def reject_sensitive(text: str) -> str | None:
    """Return a user-facing reason if the text looks like it contains highly sensitive data."""
    if not text:
        return None
    if _AADHAAR.search(text) or _LONG_NUMBER.search(text):
        return ("Please do not enter Aadhaar, bank account or other long ID numbers. "
                "CivicLens does not need them for a preliminary assessment.")
    if _SECRET_WORD.search(text):
        return "Please do not enter passwords, OTPs or card details. CivicLens never needs them."
    return None


# ---------------------------------------------------------------- uploads
ALLOWED_EXT = {".pdf": "pdf", ".txt": "text", ".md": "text", ".html": "html", ".htm": "html"}


def validate_upload(filename: str, content_type: str | None, data: bytes, max_bytes: int) -> tuple[str | None, str | None]:
    """Return (kind, error). Validates extension, size, magic bytes and text decodability."""
    name = (filename or "").lower()
    ext = "." + name.rsplit(".", 1)[-1] if "." in name else ""
    kind = ALLOWED_EXT.get(ext)
    if not kind:
        return None, f"Unsupported file type '{ext or 'none'}'. Allowed: PDF, TXT, MD, HTML."
    if not data:
        return None, "The file is empty."
    if len(data) > max_bytes:
        return None, f"The file is too large (limit {max_bytes // 1000} KB)."
    if kind == "pdf":
        if not data.startswith(b"%PDF-"):
            return None, "The file does not look like a valid PDF."
        if content_type and content_type not in ("application/pdf", "application/octet-stream"):
            return None, "The declared content type does not match a PDF."
    else:
        if b"\x00" in data:
            return None, "The file contains binary data and cannot be read as text."
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            return None, "The file is not valid UTF-8 text."
    return kind, None


# ---------------------------------------------------------------- approved domains
def is_approved_url(url: str) -> bool:
    """Only https URLs on official Indian government domains may be fetched."""
    try:
        u = urlparse(url)
    except ValueError:
        return False
    if u.scheme != "https" or not u.hostname:
        return False
    host = u.hostname.lower()
    return host.endswith(".gov.in") or host.endswith(".nic.in") or host in ("gov.in", "nic.in")


# ---------------------------------------------------------------- rate limiting
class RateLimiter:
    def __init__(self, per_minute: int):
        self.per_minute = per_minute
        self.hits: dict[str, deque] = defaultdict(deque)

    def allow(self, key: str) -> bool:
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] > 60:
            q.popleft()
        if len(q) >= self.per_minute:
            return False
        q.append(now)
        return True
