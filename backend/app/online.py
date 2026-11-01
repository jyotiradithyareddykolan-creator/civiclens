"""Opt-in online discovery and on-demand retrieval for official government sources.

Online results are draft records held only in memory. They are never merged into the
reviewed JSON catalog. Network content is untrusted and is reduced to plain text
passages before any rule extraction is attempted.
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import logging
import re
import socket
from datetime import date
from html.parser import HTMLParser
from urllib.parse import parse_qs, urlencode, urljoin, urlparse, urlunparse

import httpx

from . import fields, ingest, security
from .config import get_settings, today
from .retrieval import tokenize
from .store import get_store, Store

log = logging.getLogger("civiclens.online")

DISCOVERY_PAGES = (
    "https://www.myscheme.gov.in/search",
    "https://www.india.gov.in/search/node",
)
MYSCHEME_SEARCH_API = "https://www.myscheme.gov.in/api/apisetu/search/schemes"
MAX_RESPONSE_BYTES = 5_000_000
MAX_REDIRECTS = 3
_drafts: dict[str, dict] = {}
_cache: dict[str, tuple[str, bytes, str, str | None]] = {}


class _Links(HTMLParser):
    def __init__(self):
        super().__init__(); self.links = []; self._href = None; self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href = dict(attrs).get("href"); self._text = []

    def handle_data(self, data):
        if self._href is not None: self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._href is not None:
            self.links.append((self._href, " ".join(self._text).strip()))
            self._href = None


def _public_host(url: str) -> bool:
    if not security.is_approved_url(url): return False
    host = urlparse(url).hostname
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except OSError:
        return False
    return all(not (ipaddress.ip_address(x[4][0]).is_private or ipaddress.ip_address(x[4][0]).is_loopback or ipaddress.ip_address(x[4][0]).is_link_local or ipaddress.ip_address(x[4][0]).is_reserved) for x in infos)


def _safe_url(url: str) -> bool:
    return _public_host(url)


def _canonical(url: str) -> str:
    u = urlparse(url); return urlunparse((u.scheme, u.netloc.lower(), u.path or "/", "", u.query, ""))


def _title_from_html(data: bytes) -> str:
    text = data.decode("utf-8", errors="replace")
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    return re.sub(r"\s+", " ", m.group(1)).strip() if m else "Official government scheme information"


def _log_url(url: str) -> str:
    """Keep diagnostics useful without logging query strings or credentials."""
    u = urlparse(url)
    keys = "query_params=<redacted>" if parse_qs(u.query) else ""
    return urlunparse((u.scheme, u.netloc, u.path or "/", "", keys, ""))


def _fetch(url: str, extra_headers: dict[str, str] | None = None) -> tuple[str, bytes, str]:
    if not _safe_url(url): raise ValueError("The source URL is not an approved public government URL.")
    current = _canonical(url)
    redirect_chain = [_log_url(current)]
    for _ in range(MAX_REDIRECTS + 1):
        if not _safe_url(current): raise ValueError("A redirect left the approved public government domain.")
        headers = {"User-Agent": "CivicLens/1.0", **(extra_headers or {})}
        r = httpx.get(current, timeout=10.0, follow_redirects=False, headers=headers)
        content_type = r.headers.get("content-type", "")
        log.info("official_fetch status=%s final_url=%s content_type=%s bytes=%s redirects=%s generic_error_shell=%s",
                 r.status_code, _log_url(current), content_type.split(";", 1)[0], len(r.content), redirect_chain,
                 _is_error_shell(r.content))
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("location")
            if not location: raise ValueError("The source returned an invalid redirect.")
            current = _canonical(urljoin(current, location)); redirect_chain.append(_log_url(current)); continue
        if r.status_code != 200: raise ValueError(f"The official source returned HTTP {r.status_code}.")
        if len(r.content) > MAX_RESPONSE_BYTES: raise ValueError("The official source is larger than the safe retrieval limit.")
        return current, r.content, content_type
    raise ValueError("The official source redirected too many times.")


def _match(text: str, query: str) -> bool:
    q = set(tokenize(query)); return not q or bool(q & set(tokenize(text)))


def discover(query: str, limit: int = 5) -> dict:
    leads, seen, failures = [], set(), []

    # myScheme's visible search page is client-rendered. Use the public endpoint
    # called by that page first; its descriptions remain discovery metadata, not
    # eligibility evidence.
    try:
        api_url = MYSCHEME_SEARCH_API + "?" + urlencode({"lang": "en", "q": "[]", "keyword": query, "sort": "", "from": 0, "size": limit})
        _, data, _ = _fetch(api_url)
        payload = __import__("json").loads(data.decode("utf-8", errors="replace"))
        records = payload.get("data", {}).get("hits", {}).get("items", [])
        for record in records:
            f = record.get("fields", {})
            slug = f.get("slug")
            title = f.get("schemeName")
            if not slug or not title:
                continue
            target = _canonical("https://www.myscheme.gov.in/schemes/" + str(slug).strip("/"))
            if target in seen:
                continue
            seen.add(target)
            local = any(target == d.get("url") for s in get_store().schemes.values() for d in s.get("documents", []))
            leads.append({"name": title, "authority": f.get("nodalDepartmentName") or "Government authority",
                          "source_url": target, "source_type": "official scheme page", "retrieved": False,
                          "already_local": local, "description": f.get("briefDescription") or "Discovery lead; eligibility is not established from search relevance.",
                          "source_passages": []})
    except (ValueError, KeyError, TypeError, httpx.HTTPError, OSError) as e:
        failures.append(type(e).__name__)

    if len(leads) >= limit:
        return {"results": leads[:limit], "failures": failures, "online": True,
                "state": "official_results",
                "notice": "Official results discovered. Search relevance is not eligibility evidence; retrieve official details before assessing eligibility."}

    for page in DISCOVERY_PAGES:
        try:
            url = page + "?" + urlencode({"keyword": query, "keys": query})
            _, data, _ = _fetch(url)
            parser = _Links(); parser.feed(data.decode("utf-8", errors="replace"))
            for href, title in parser.links:
                target = _canonical(urljoin(page, href))
                if (not security.is_approved_url(target) or not _safe_url(target) or target in seen
                        or not title or not _match(title, query)): continue
                seen.add(target)
                local = any(target == d.get("url") for s in get_store().schemes.values() for d in s.get("documents", []))
                leads.append({"name": title, "authority": urlparse(target).hostname, "source_url": target,
                              "source_type": "official scheme page", "retrieved": False,
                              "already_local": local, "description": "Discovery lead; eligibility is not established from search relevance.",
                              "source_passages": []})
                if len(leads) >= limit: break
        except (ValueError, httpx.HTTPError, OSError) as e:
            failures.append(type(e).__name__)
    state = "official_results" if leads else ("source_failure" if failures else "no_official_results")
    notice = {
        "official_results": "Official results discovered. Search relevance is not eligibility evidence; retrieve official details before assessing eligibility.",
        "source_failure": "Official-source search could not be completed. No online result is being treated as evidence.",
        "no_official_results": "No official results were found for this search. This does not mean the scheme does not exist elsewhere.",
    }[state]
    return {"results": leads[:limit], "failures": failures, "online": True, "state": state,
            "notice": notice}


def _legacy_rule_candidates(text: str, doc_id: str) -> list[dict]:
    rules = []
    patterns = [
        ("income", r"(?:income|earnings)[^.!?]{0,100}(?:₹|Rs\.?|INR)?\s*([\d,]+)\s*(?:lakh|lakhs)?", "annual_income", "lte"),
        ("age", r"age[^.!?]{0,50}(?:between|from)\s*(\d+)\s*(?:and|to)\s*(\d+)", "age", "between"),
        ("age", r"(?:(?:age|aged)[^.!?]{0,40}(?:above|over|more than)|(?:above|over|more than))\s*(\d+)\s*years?", "age", "gt"),
        ("landholding", r"(?:up to|upto|not more than)\s*([\d.]+)\s*hectares?", "landholding_hectares", "lte"),
    ]
    for i, (criterion, pat, attr, op) in enumerate(patterns):
        for p in re.finditer(pat, text, re.I):
            evidence = p.group(0).strip(); value = int(p.group(1).replace(",", ""))
            if criterion == "income" and "lakh" in evidence.lower(): value *= 100000
            if op == "between": value = [int(p.group(1)), int(p.group(2))]
            rules.append({"id": f"r{i+1}", "criterion": criterion, "label": criterion.title(), "attribute": attr,
                          "op": op, "value": value, "evidence": evidence, "mandatory": True,
                          "doc_id": doc_id, "passage_id": "p1"})
            break
    return rules


def _rule_candidates(passages: list[dict], doc_id: str) -> list[dict]:
    """Extract explicit requirements from retrieved passages only."""
    rules: list[dict] = []
    used: set[str] = set()
    state_pattern = "|".join(re.escape(s) for s in fields.STATES)
    patterns = [
        ("income", r"(?:annual|family|household)?\s*income[^.!?]{0,100}?(?:Rs\.?|INR|₹)?\s*([\d,]+(?:\.\d+)?)\s*(lakh|lakhs|crore|crores)?", "annual_income", "lte"),
        ("age", r"age[^.!?]{0,50}(?:between|from)\s*(\d+)\s*(?:and|to)\s*(\d+)", "age", "between"),
        ("age", r"(?:aged|age)\s*(\d+)\s*(?:years?|yrs?)(?:\s*(?:of age)?\s*(?:and|or)\s*above)?", "age", "gte"),
        ("age", r"(?:(?:age|aged)[^.!?]{0,40}(?:above|over|more than)|(?:above|over|more than))\s*(\d+)\s*years?", "age", "gt"),
        ("landholding", r"(?:up to|upto|not more than|maximum of)\s*([\d.]+)\s*hectares?", "landholding_hectares", "lte"),
        ("residence", rf"(?:resident|residing|domiciled|domicile)[^.!?]{{0,40}}\b({state_pattern})\b", "state", "eq"),
        ("category", r"\b(scheduled caste|sc|scheduled tribe|st|other backward classes|obc|economically weaker sections|ews|ebc|dnt)\b", "category", "eq"),
    ]
    category_values = {"scheduled caste": "sc", "sc": "sc", "scheduled tribe": "st", "st": "st",
                       "other backward classes": "obc", "obc": "obc", "economically weaker sections": "ews",
                       "ews": "ews", "ebc": "ebc_dnt", "dnt": "ebc_dnt"}
    for passage in passages:
        text = passage.get("text", "")
        for criterion, pat, attr, op in patterns:
            if criterion in used:
                continue
            match = re.search(pat, text, re.I)
            if not match:
                continue
            evidence = match.group(0).strip()
            value = match.group(1).replace(",", "")
            if criterion == "income":
                value = float(value) if "." in value else int(value)
                multiplier = (match.group(2) or "").lower()
                value *= 100000 if multiplier in ("lakh", "lakhs") else 10000000 if multiplier in ("crore", "crores") else 1
            elif op == "between":
                value = [int(match.group(1)), int(match.group(2))]
            elif criterion == "landholding":
                value = float(value) if "." in value else int(value)
            elif criterion == "category":
                value = category_values[value.lower()]
            elif criterion == "residence":
                value = value
            else:
                value = int(value)
            rules.append({"id": f"r{len(rules) + 1}", "criterion": criterion, "label": criterion.title(),
                          "attribute": attr, "op": op, "value": value, "evidence": evidence, "mandatory": True,
                          "doc_id": doc_id, "passage_id": passage["id"]})
            used.add(criterion)
    if "residence" not in used:
        for passage in passages:
            match = re.search(r"(?:resident|residing|domiciled|citizen)[^.!?]{0,40}\bIndia\b", passage.get("text", ""), re.I)
            if match:
                rules.append({"id": f"r{len(rules) + 1}", "criterion": "residence", "label": "Residence",
                              "attribute": "state", "op": "eq", "value": None, "evidence": match.group(0).strip(),
                              "mandatory": True, "manual_check": True, "doc_id": doc_id, "passage_id": passage["id"]})
                break
    return rules


def _is_error_shell(data: bytes) -> bool:
    text = re.sub(r"\s+", " ", data.decode("utf-8", errors="replace")).lower()
    return "something went wrong. please try again later" in text


def _json_source_text(value) -> str:
    """Flatten JSON string values without treating field names or snippets as rules."""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, list):
        return "\n".join(x for x in (_json_source_text(v) for v in value) if x)
    if isinstance(value, dict):
        return "\n".join(x for x in (_json_source_text(v) for v in value.values()) if x)
    return ""


def _myscheme_detail_text(url: str, data: bytes) -> tuple[bytes, str, str] | None:
    """Use myScheme's public detail API when its rendered page is only an error shell.

    The credential is supplied by the operator through
    CIVICLENS_MYSCHEME_API_KEY; it is never returned to the browser.
    """
    parsed = urlparse(url)
    if parsed.hostname != "www.myscheme.gov.in" or "/schemes/" not in parsed.path:
        return None
    if not _is_error_shell(data):
        return None
    key = get_settings().myscheme_api_key
    if not key:
        return None
    slug = parsed.path.rstrip("/").split("/schemes/", 1)[1]
    if not slug or "/" in slug:
        return None
    api_url = "https://api.myscheme.gov.in/schemes/v6/public/schemes"
    if not _safe_url(api_url):
        return None
    response = httpx.post(api_url, json=[slug], timeout=10.0, follow_redirects=False,
                          headers={"User-Agent": "CivicLens/1.0", "x-api-key": key})
    log.info("official_detail_api status=%s final_url=%s content_type=%s bytes=%s slug=%s",
             response.status_code, _log_url(api_url), response.headers.get("content-type", "").split(";", 1)[0],
             len(response.content), slug)
    if response.status_code != 200:
        raise ValueError(f"The official myScheme detail API returned HTTP {response.status_code} for this scheme.")
    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ValueError("The official myScheme detail API response is larger than the safe retrieval limit.")
    try:
        payload = response.json()
    except ValueError:
        raise ValueError("The official myScheme detail API returned invalid JSON for this scheme.") from None
    rows = payload.get("data") or []
    if not rows:
        raise ValueError("The official myScheme detail API returned no scheme content for this slug.")
    en = rows[0].get("en") or {}
    basic = en.get("basicDetails") or {}
    content = en.get("schemeContent") or {}
    parts = [basic.get("schemeName") or "", content.get("briefDescription") or ""]
    text = "\n".join(x for x in parts if x).strip()
    if not text:
        raise ValueError("The official myScheme detail API returned an empty scheme record.")
    return text.encode("utf-8"), "text/plain", api_url


def retrieve(lead: dict) -> dict:
    url = lead["source_url"]
    key = _canonical(url)
    detail_url = None
    if key in _cache: final_url, data, content_type, detail_url = _cache[key]
    else:
        final_url, data, content_type = _fetch(url)
        detail = _myscheme_detail_text(final_url, data)
        if detail:
            data, content_type, detail_url = detail
        else:
            detail_url = None
            if _is_error_shell(data):
                raise ValueError("The official scheme page returned a generic error page; no source evidence was retrieved. Configure CIVICLENS_MYSCHEME_API_KEY to try the official myScheme detail API.")
        _cache[key] = (final_url, data, content_type, detail_url)
    name = lead.get("name") or _title_from_html(data)
    ctype = content_type.lower()
    if data.startswith(b"%PDF-") or "pdf" in ctype:
        kind = "pdf"
    elif "json" in ctype:
        kind = "json"
    elif "html" in ctype or not ctype or urlparse(url).path.lower().endswith((".html", ".htm")) or data.lstrip().startswith(b"<"):
        kind = "html"
    elif ctype.startswith("text/") or urlparse(url).path.lower().endswith((".txt", ".md")):
        kind = "text"
    else:
        raise ValueError("The official source returned an unsupported content type.")
    if kind == "json":
        try:
            text = _json_source_text(json.loads(data.decode("utf-8")))
        except (UnicodeDecodeError, ValueError, TypeError):
            raise ValueError("The official JSON source could not be parsed safely.") from None
        if not text:
            raise ValueError("The official JSON source contained no readable scheme content.")
    else:
        suffix = {"pdf": ".pdf", "html": ".html", "text": ".txt"}[kind]
        validation_name = url if urlparse(url).path.lower().endswith((".pdf", ".txt", ".md", ".html", ".htm")) else url + suffix
        valid_kind, error = security.validate_upload(validation_name, content_type.split(";", 1)[0] or None, data, MAX_RESPONSE_BYTES)
        if error: raise ValueError(error)
        text = ingest.extract_text(valid_kind, data)
    passages = ingest.chunk_text(text)
    for p in passages: p.update(verbatim=True, excerpt=p["text"])
    doc_id = "online-doc-" + hashlib.sha256(final_url.encode()).hexdigest()[:12]
    sid = "ONLINE-" + hashlib.sha256(final_url.encode()).hexdigest()[:12]
    doc = {"id": doc_id, "title": name, "authority": lead.get("authority") or "Official government authority",
           "version": 1, "doc_type": "official scheme page", "publication_date": None, "effective_date": None,
           "status": "unclear", "last_checked": today().isoformat(), "url": final_url, "manual_verification": True,
           "reading_note": ("Retrieved from the official myScheme detail API because the HTML page returned an error shell; "
                            "exact source wording was extracted, but a human has not reviewed this draft." if detail_url else
                            "Retrieved on demand; exact source wording was extracted, but a human has not reviewed this draft."),
           "retrieval_source_url": detail_url,
           "retrieval_status": "ok", "facts": {}, "passages": passages}
    rules = _rule_candidates(passages, doc_id)
    draft = {"id": sid, "name": name, "authority": doc["authority"], "category": "citizens", "target_groups": ["citizens"],
             "scheme_type": "grant", "states": ["all"], "geography": "India", "description": "Draft scheme record from an official source.",
             "description_hi": "", "keywords": tokenize(name), "aliases": [], "portal": {"name": "Official source", "url": final_url, "verified": True, "note": "Source retrieved on demand."},
             "application": {}, "documents": [doc], "rules": rules, "required_documents": [], "coverage": "partial",
             "unresolved": ["Draft extraction requires human review; unsupported criteria are unknown."], "online_draft": True}
    _drafts[sid] = draft
    Store({"schemes": [draft]})
    message = ("Official content retrieved into an unreviewed draft and explicit criteria were extracted. Eligibility remains preliminary."
               if rules else
               "Official content retrieved, but no explicit eligibility criteria could be extracted from it. Eligibility is undetermined.")
    return {"scheme": draft, "draft_id": sid, "retrieved": True, "source_coverage": "partial", "rules_extracted": len(rules),
            "message": message}


def draft(scheme_id: str) -> dict | None: return _drafts.get(scheme_id)


def draft_store(scheme_id: str) -> Store | None:
    s = draft(scheme_id); return Store({"schemes": [s]}) if s else None
