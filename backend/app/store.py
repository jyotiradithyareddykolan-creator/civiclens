"""Loads the scheme dataset and verifies that every extracted rule is grounded in its cited passage.

Persistence approach (documented in the README): the demo uses a read-only JSON file loaded into memory.
User profiles are never stored server-side.
"""
import json
import re
import threading
from pathlib import Path

from . import security
from .config import get_settings


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


class Store:
    def __init__(self, data: dict):
        self.meta = data.get("meta", {})
        self.catalog = data.get("document_catalog", {})
        self.schemes: dict[str, dict] = {}
        self.doc_index: dict[str, tuple[str, dict]] = {}
        for s in data.get("schemes", []):
            self._prepare(s)
            self.schemes[s["id"]] = s

    # ------------------------------------------------------------------ preparation
    def _prepare(self, scheme: dict) -> None:
        for d in scheme.get("documents", []):
            d.setdefault("passages", [])
            d.setdefault("facts", {})
            d.setdefault("retrieval_status", "ok")
            pmap = {}
            for p in d["passages"]:
                hits = security.scan_text(p.get("text", "")) or security.scan_text(p.get("section", ""))
                p["flagged"] = bool(hits)
                p["flags"] = hits
                pmap[p["id"]] = p
            d["_pmap"] = pmap
            self.doc_index[d["id"]] = (scheme["id"], d)

        for r in scheme.get("rules", []):
            r["verified"] = self._grounded(r, scheme) and not r.get("ambiguous", False)
        for q in scheme.get("required_documents", []):
            q["verified"] = self._grounded(q, scheme)
            how = q.get("how_to_obtain")
            if how:
                p = self.passage(how["doc_id"], how["passage_id"])
                how["verified"] = bool(p and not p["flagged"])

    def _grounded(self, item: dict, scheme: dict) -> bool:
        """An extracted item is verified only if its evidence snippet appears verbatim in a clean passage.

        Passages that are summaries (not quoted text) carry "verbatim": false and can never verify an item.
        """
        p = self.passage(item["doc_id"], item["passage_id"])
        if not p or p["flagged"] or p.get("verbatim", True) is False:
            return False
        return bool(item.get("evidence")) and norm(item["evidence"]) in norm(p["text"])

    # ------------------------------------------------------------------ lookups
    def scheme(self, scheme_id: str) -> dict | None:
        return self.schemes.get(scheme_id)

    def doc(self, doc_id: str) -> dict | None:
        hit = self.doc_index.get(doc_id)
        return hit[1] if hit else None

    def passage(self, doc_id: str, passage_id: str) -> dict | None:
        d = self.doc(doc_id)
        return d["_pmap"].get(passage_id) if d else None

    def doc_name(self, key: str, lang: str) -> str:
        c = self.catalog.get(key)
        if not c:
            return key.replace("_", " ").capitalize()
        return c["name_hi"] if lang == "hi" and c.get("name_hi") else c["name"]


_store: Store | None = None
_lock = threading.Lock()


def load_data(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def get_store() -> Store:
    global _store
    with _lock:
        if _store is None:
            _store = Store(load_data(get_settings().data_path))
        return _store


def reload_store(data: dict | None = None) -> Store:
    """Reload from disk, or from an in-memory dict (used by tests)."""
    global _store
    with _lock:
        _store = Store(data if data is not None else load_data(get_settings().data_path))
        return _store
