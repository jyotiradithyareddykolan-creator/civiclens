"""Data-verification report: what is verified, partially verified or unverified for every scheme.

    python -m app.report [path/to/schemes.json] [--json]

"Quote matches stored excerpt" means the rule's evidence text is found inside a stored VERBATIM passage. It does NOT
mean the stored passage was compared with the original government document; that needs a person
(documents are marked manual_verification until then).
"""
import json
import re
import sys
from pathlib import Path

from .config import get_settings
from .store import Store, load_data

OFFICIAL_HOST = re.compile(r"^https://([a-z0-9-]+\.)*(gov|nic)\.in/", re.I)


def scheme_report(store: Store, s: dict) -> dict:
    docs = []
    for d in s["documents"]:
        verbatim = [p for p in d["passages"] if p.get("verbatim", True) is not False]
        docs.append({
            "id": d["id"], "title": d["title"], "type": d.get("doc_type"), "url": d.get("url"),
            "official_domain": bool(d.get("url") and OFFICIAL_HOST.match(d["url"])),
            "publication_date": d.get("publication_date"), "effective_date": d.get("effective_date"),
            "status": d.get("status"), "last_checked": d.get("last_checked"),
            "is_guideline": d.get("doc_type") in ("scheme guidelines", "guidelines"),
            "manual_verification_required": bool(d.get("manual_verification")),
            "passages_total": len(d["passages"]), "passages_verbatim": len(verbatim),
            "passages_summary_only": len(d["passages"]) - len(verbatim),
        })
    rules = []
    for r in s["rules"]:
        p = store.passage(r["doc_id"], r["passage_id"])
        rules.append({
            "id": r["id"], "criterion": r["criterion"], "op": r["op"], "value": r["value"], "mandatory": r["mandatory"],
            "quote_matches_stored_excerpt": bool(r.get("verified")),
            "evidence_type": "verbatim" if p and p.get("verbatim", True) is not False else "summary",
            "manual_check": bool(r.get("manual_check")), "ambiguous": bool(r.get("ambiguous")),
        })
    reqs = [{"id": q["id"], "key": q["key"], "classification": q["classification"],
             "quote_matches_stored_excerpt": bool(q.get("verified"))} for q in s["required_documents"]]
    n_ok = sum(1 for r in rules if r["quote_matches_stored_excerpt"] and not r["manual_check"])
    portal = s.get("portal") or {}
    return {
        "id": s["id"], "name": s["name"], "authority": s["authority"], "coverage": s.get("coverage") or "not_declared",
        "validity": s.get("validity") or "not_declared", "validity_note": s.get("validity_note"),
        "documents": docs, "rules": rules, "required_documents": reqs, "unresolved": s.get("unresolved") or [],
        "counts": {"rules": len(rules), "rules_testable_and_quote_matched": n_ok,
                   "rules_sourced_but_not_testable": sum(1 for r in rules if r["manual_check"] and r["quote_matches_stored_excerpt"]),
                   "rules_unverified": sum(1 for r in rules if not r["quote_matches_stored_excerpt"]),
                   "requirements": len(reqs), "requirements_unverified": sum(1 for q in reqs if not q["quote_matches_stored_excerpt"])},
        "application_url": {"portal_url": portal.get("url"), "verified_scheme_specific_application_page": False,
                            "note": "Only the general portal is linked; no scheme-specific application page has been verified."},
    }


def build_report(path: Path | None = None) -> dict:
    data = load_data(path or get_settings().data_path)
    store = Store(data)
    return {"dataset": str(path or get_settings().data_path), "read_on": store.meta.get("read_on"),
            "sources_not_readable": store.meta.get("sources_not_readable", []),
            "schemes": [scheme_report(store, s) for s in store.schemes.values()]}


def to_markdown(rep: dict) -> str:
    out = ["# Data verification report", "",
           "No document below has been compared word for word with the original by a person. "
           "'Quote matches stored excerpt' only means the rule's evidence text is inside a stored verbatim passage.", ""]
    for s in rep["schemes"]:
        c = s["counts"]
        out += [f"## {s['name']} (`{s['id']}`)", f"- Authority: {s['authority']}",
                f"- Source coverage: **{s['coverage']}** · Current validity: **{s['validity']}**" + (f" ({s['validity_note']})" if s["validity_note"] else ""),
                f"- Rules: {c['rules']} total; {c['rules_testable_and_quote_matched']} testable and quote-matched; "
                f"{c['rules_sourced_but_not_testable']} sourced but not testable here; {c['rules_unverified']} unverified",
                f"- Required documents: {c['requirements']} listed; {c['requirements_unverified']} unverified"]
        for d in s["documents"]:
            kind = "guidelines" if d["is_guideline"] else (d["type"] or "other")
            out.append(f"- Source: {d['title']} · {kind} · official domain: {'yes' if d['official_domain'] else 'NO'} · "
                       f"published {d['publication_date'] or 'not stated'} · effective {d['effective_date'] or 'not stated'} · "
                       f"{d['passages_verbatim']} verbatim / {d['passages_summary_only']} summary-only passages · {d['url']}")
        out.append(f"- Application page: {s['application_url']['note']}")
        for u in s["unresolved"]:
            out.append(f"- Unresolved: {u}")
        out.append("")
    if rep["sources_not_readable"]:
        out += ["## Sources that could not be read", *[f"- {u}" for u in rep["sources_not_readable"]], ""]
    return "\n".join(out)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    rep = build_report(Path(args[0]) if args else None)
    print(json.dumps(rep, indent=2, ensure_ascii=False) if "--json" in sys.argv else to_markdown(rep))
