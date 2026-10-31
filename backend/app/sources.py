"""Source freshness flags and (optional, allow-listed) live source checks."""
import hashlib
import time
from datetime import date

from .config import get_settings, today
from .i18n import t
from .security import is_approved_url


def doc_summary(doc: dict) -> dict:
    return {k: doc.get(k) for k in ("id", "title", "authority", "version", "doc_type", "publication_date",
                                    "effective_date", "last_checked", "status", "url", "demo", "manual_verification", "reading_note")}


def doc_flags(doc: dict, lang: str = "en") -> list[dict]:
    """Flag documents whose current validity is unestablished, stale, unavailable or superseded.

    A 'last checked' date is never treated as proof that a policy is current.
    """
    s = get_settings()
    title = doc.get("title", doc["id"])
    flags = []

    def add(code, severity, key, **kw):
        flags.append({"code": code, "severity": severity, "doc_id": doc["id"], "message": t(lang, key, title=title, **kw)})

    if doc.get("retrieval_status", "ok") != "ok":
        add("unavailable", "error", "warn_unavailable")
        return flags
    if doc.get("status") == "superseded":
        add("superseded", "info", "warn_superseded")
    elif doc.get("status") == "unclear":
        add("unclear_validity", "warning", "warn_unclear")
    elif not doc.get("effective_date"):
        add("validity_not_established", "warning", "warn_no_effective")

    pub = doc.get("publication_date")
    if pub and not doc.get("effective_date") and doc.get("status") != "superseded":
        try:
            if (today() - date.fromisoformat(pub)).days > 730:
                add("older_source", "info", "warn_older", date=pub)
        except ValueError:
            pass
    if doc.get("manual_verification"):
        add("manual_verification_required", "warning", "warn_manual_verify")

    lc = doc.get("last_checked")
    if not lc:
        add("never_checked", "warning", "warn_never_checked")
    else:
        try:
            age = (today() - date.fromisoformat(lc)).days
        except ValueError:
            age = None
        if age is not None and age > s.stale_days:
            add("stale", "warning", "warn_stale", date=lc, days=s.stale_days)
    return flags


def check_source(doc: dict, lang: str = "en") -> dict:
    """Check whether a source can be retrieved. Never invents a result; never writes to the dataset."""
    s = get_settings()
    base = {"doc_id": doc["id"], "checked_on": today().isoformat(), "url": doc.get("url")}

    if doc.get("fetch_mode") == "simulate_unavailable":
        return {**base, "status": "unavailable", "message": t(lang, "fetch_unavailable"), "retry_allowed": True}
    url = doc.get("url")
    if not url:
        return {**base, "status": "not_checked", "message": t(lang, "fetch_not_checked"), "retry_allowed": False}
    if not s.live_fetch:
        return {**base, "status": "not_checked", "message": t(lang, "fetch_disabled"), "retry_allowed": False}
    if not is_approved_url(url):
        return {**base, "status": "blocked", "message": t(lang, "fetch_blocked"), "retry_allowed": False}

    import httpx  # imported lazily so the demo runs without network use

    last_error = "unknown"
    for attempt in range(3):  # bounded retries
        try:
            r = httpx.get(url, timeout=10.0, follow_redirects=False, headers={"User-Agent": "CivicLens/1.0"})
            if r.status_code == 200:
                return {**base, "status": "ok", "message": t(lang, "fetch_ok"), "retry_allowed": False,
                        "content_sha256": hashlib.sha256(r.content).hexdigest(), "bytes": len(r.content)}
            last_error = f"HTTP {r.status_code}"
        except httpx.HTTPError as e:
            last_error = type(e).__name__
        time.sleep(0.5 * (attempt + 1))
    return {**base, "status": "unavailable", "message": t(lang, "fetch_unavailable"), "retry_allowed": True,
            "detail": last_error}


def collapse_flags(flags: list[dict], lang: str = "en") -> list[dict]:
    """Show 'manual verification required' once per scheme instead of once per document."""
    out, seen = [], False
    for f in flags:
        if f["code"] == "manual_verification_required":
            if seen:
                continue
            seen = True
            f = {**f, "doc_id": None, "message": t(lang, "warn_manual_verify_scheme")}
        out.append(f)
    return out
