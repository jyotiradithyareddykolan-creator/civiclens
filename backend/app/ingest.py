"""Document ingestion for curators: extract text, split into passages, keep metadata.

Usage (local, for curators adding real schemes):
    python -m app.ingest path/to/guidelines.pdf --title "..." --authority "..." --url https://... --out draft.json

The draft is NOT automatically trusted: a curator must add rules/required documents with evidence quotes
(see README "Adding real schemes"). Raw document content is never logged.
"""
import argparse
import hashlib
import io
import json
import re
import sys
from datetime import date
from html.parser import HTMLParser

from . import security

MAX_PDF_PAGES = 200
HEADING_RE = re.compile(r"^(?:\d+(?:\.\d+)*[.)]?\s+\S.{0,78}|[A-Z][A-Z \-/&]{4,60})$")


class _Text(HTMLParser):
    BLOCK = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "table"}

    def __init__(self):
        super().__init__()
        self.out, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self.skip = max(0, self.skip - 1)
        elif tag in self.BLOCK:
            self.out.append("\n")

    def handle_data(self, data):
        if not self.skip:
            self.out.append(data)


def extract_text(kind: str, data: bytes) -> str:
    if kind == "pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(io.BytesIO(data))
            pages = reader.pages[:MAX_PDF_PAGES]
            return "\n".join((p.extract_text() or "") for p in pages)
        except Exception as e:  # noqa: BLE001 - any parser failure is reported generically
            raise ValueError(f"The PDF could not be parsed ({type(e).__name__}). Scanned PDFs need OCR, which is not supported yet.") from None
    text = data.decode("utf-8", errors="replace")
    if kind == "html":
        p = _Text()
        p.feed(text)
        text = "".join(p.out)
    return text


def chunk_text(text: str, max_chars: int = 700) -> list[dict]:
    """Split into passages, tracking the most recent heading as the section reference."""
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in text.splitlines()]
    passages, section, buf = [], "Untitled", []

    def flush():
        nonlocal buf
        body = " ".join(buf).strip()
        if body:
            passages.append({"id": f"p{len(passages) + 1}", "section": section, "text": body})
        buf = []

    for ln in lines:
        if not ln:
            if sum(len(x) for x in buf) > max_chars * 0.6:
                flush()
            continue
        if HEADING_RE.match(ln) and len(ln) < 80 and not ln.endswith("."):
            flush()
            section = ln
            continue
        if sum(len(x) + 1 for x in buf) + len(ln) > max_chars:
            flush()
        buf.append(ln)
    flush()
    return passages


def inspect_bytes(kind: str, data: bytes) -> dict:
    """Metadata-only summary used by the API. Never returns raw content (privacy: AC-11)."""
    text = extract_text(kind, data)
    passages = chunk_text(text)
    clean, flagged = security.split_passages(passages)
    return {
        "kind": kind, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        "text_extracted": bool(text.strip()), "passage_count": len(passages),
        "clean_passage_count": len(clean), "flagged_passage_count": len(flagged),
        "note": None if text.strip() else "No text could be extracted. If this is a scanned document, OCR is not supported in this version.",
    }


def build_draft(kind: str, data: bytes, title: str, authority: str, url: str | None, publication_date: str | None = None) -> dict:
    text = extract_text(kind, data)
    passages = chunk_text(text)
    return {
        "id": "d-" + hashlib.sha1((url or title).encode()).hexdigest()[:8], "title": title, "authority": authority,
        "doc_type": "guidelines", "version": 1, "publication_date": publication_date, "effective_date": None,
        "status": "validity_not_established", "last_checked": date.today().isoformat(), "url": url, "demo": False,
        "fetch_mode": "static", "retrieval_status": "ok", "facts": {}, "passages": passages,
        "curator_todo": "Add rules, required_documents and facts with verbatim evidence quotes; confirm effective date and supersession.",
        "url_on_approved_domain": bool(url and security.is_approved_url(url)),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Create a draft document record from a PDF/HTML/TXT file.")
    ap.add_argument("path")
    ap.add_argument("--title", required=True)
    ap.add_argument("--authority", required=True)
    ap.add_argument("--url")
    ap.add_argument("--publication-date")
    ap.add_argument("--out", default="draft_document.json")
    a = ap.parse_args(argv)
    name = a.path.lower()
    kind = "pdf" if name.endswith(".pdf") else "html" if name.endswith((".html", ".htm")) else "text"
    with open(a.path, "rb") as f:
        data = f.read()
    k, err = security.validate_upload(a.path, None, data, 25_000_000)
    if err:
        print("Rejected:", err, file=sys.stderr)
        return 2
    draft = build_draft(k, data, a.title, a.authority, a.url, a.publication_date)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(draft, f, indent=2, ensure_ascii=False)
    print(f"Wrote {a.out}: {len(draft['passages'])} passages. Review it, then add rules/evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
