"""Personalised document checklist built only from documented requirements."""
from datetime import date

from . import fields
from .config import today
from .eligibility import eval_op, get_attr, select_docs
from .i18n import t
from .sources import doc_flags
from .store import get_store

CLASS_RANK = {"mandatory": 0, "conditional": 1, "optional": 2, "unverified": 3}


def _cite(q: dict, store) -> dict:
    d = store.doc(q["doc_id"])
    p = store.passage(q["doc_id"], q["passage_id"])
    return {"doc_id": d["id"], "passage_id": q["passage_id"], "doc_title": d["title"], "authority": d["authority"],
            "section": p["section"] if p else None, "text": None if (not p or p["flagged"]) else p["text"],
            "evidence": q.get("evidence"), "flagged": bool(p and p["flagged"]), "demo": d.get("demo", False),
            "excerpt": bool(p and p.get("excerpt")), "verbatim": (p.get("verbatim", True) if p else True),
            "publication_date": d.get("publication_date"), "last_checked": d.get("last_checked"), "url": d.get("url")}


def build_checklist(scheme: dict, profile: dict, lang: str = "en", doc_ids: list[str] | None = None) -> dict:
    store = get_store()
    active, _ = select_docs(scheme, doc_ids)
    usable = [d for d in active if d.get("retrieval_status", "ok") == "ok"]
    usable_ids = [d["id"] for d in usable]
    user_docs = profile.get("documents") or {}

    reqs = [q for q in scheme.get("required_documents", []) if q["doc_id"] in usable_ids]
    by_key: dict[str, list[dict]] = {}
    for q in reqs:
        by_key.setdefault(q["key"], []).append(q)

    items, not_applicable, follow_ups = [], [], {}
    for key, group in by_key.items():
        verified = [q for q in group if q.get("verified")]
        cls_raw = min((q["classification"] for q in (verified or group)), key=lambda c: CLASS_RANK.get(c, 9)) if verified else "unverified"
        use = verified[0] if verified else group[0]
        listed_in = {q["doc_id"] for q in group}
        disagreement = len(usable_ids) > 1 and listed_in != set(usable_ids)

        applies = "applies"
        cond_note = None
        if verified and cls_raw == "conditional" and use.get("condition"):
            c = use["condition"]
            res = eval_op(c["op"], get_attr(profile, c["attribute"]), c["value"])
            applies = "unknown" if res is None else ("applies" if res else "not_applicable")
            if applies == "unknown" and c["attribute"] in fields.FIELD_SPECS:
                follow_ups[c["attribute"]] = {"attribute": c["attribute"], "question": fields.question(c["attribute"], lang)}
        if use.get("condition_note"):
            cond_note = use["condition_note_hi"] if lang == "hi" and use.get("condition_note_hi") else use["condition_note"]

        user_status = user_docs.get(key, "not_confirmed")
        how = None
        for q in group:
            h = q.get("how_to_obtain")
            if h and h.get("verified"):
                how = {"text": h["text_hi"] if lang == "hi" and h.get("text_hi") else h["text"],
                       "citation": _cite({**q, "doc_id": h["doc_id"], "passage_id": h["passage_id"], "evidence": None}, store)}
                break

        if applies == "not_applicable":
            next_action = ""
        elif applies == "unknown":
            next_action = t(lang, "na_conditional_unknown")
        elif user_status == "available":
            next_action = t(lang, "na_available")
        elif user_status == "missing":
            next_action = t(lang, "na_missing_with_how" if how else "na_missing_no_how")
        else:
            next_action = t(lang, "na_not_confirmed")

        item = {
            "key": key, "name": store.doc_name(key, lang), "classification": cls_raw,
            "classification_label": t(lang, f"cl_{cls_raw}"), "applies": applies, "applies_label": t(lang, f"app_{applies}"),
            "condition_note": cond_note, "user_status": user_status, "user_status_label": t(lang, f"ds_{user_status}"),
            "next_action": next_action, "instructions": how,
            "source_disagreement": t(lang, "source_disagreement") if disagreement else None,
            "citations": [_cite(q, store) for q in group], "verified": bool(verified),
        }
        (not_applicable if applies == "not_applicable" else items).append(item)

    items.sort(key=lambda i: (CLASS_RANK.get(i["classification"], 9), i["name"]))
    counted = [i for i in items if i["applies"] == "applies" and i["classification"] in ("mandatory", "conditional")]
    counts = {
        "required": len(counted),
        "available": sum(i["user_status"] == "available" for i in counted),
        "missing": sum(i["user_status"] == "missing" for i in counted),
        "not_confirmed": sum(i["user_status"] == "not_confirmed" for i in counted),
        "to_clarify": sum(i["applies"] == "unknown" for i in items),
    }

    # deadline from usable documents' facts (never guessed)
    deadline = None
    for d in usable:
        f = d.get("facts", {}).get("deadline")
        if f:
            p = store.passage(d["id"], f["passage_id"])
            passed = None
            if f.get("date"):
                try:
                    passed = date.fromisoformat(f["date"]) < today()
                except ValueError:
                    pass
            deadline = {"text": f["value"], "date": f.get("date"), "passed": passed, "doc_id": d["id"],
                        "passage_id": f["passage_id"], "passage_text": p["text"] if p and not p["flagged"] else None,
                        "note": t(lang, "deadline_passed") if passed else None}
    warnings = []
    for d in active:
        warnings.extend(doc_flags(d, lang))

    portal = scheme.get("portal")
    if portal:
        portal = {**portal, "note": portal["note_hi"] if lang == "hi" and portal.get("note_hi") else portal.get("note")}

    return {
        "scheme_id": scheme["id"], "scheme_name": scheme["name"], "language": lang, "generated_on": today().isoformat(),
        "items": items, "not_applicable": not_applicable, "counts": counts, "deadline": deadline,
        "deadline_note": None if deadline else t(lang, "no_deadline"),
        "portal": portal, "application_link": None, "application_link_note": t(lang, "no_link"),
        "follow_up_questions": list(follow_ups.values()), "warnings": warnings,
        "disclaimer": t(lang, "disclaimer"), "doc_ids_used": usable_ids,
    }


def application_guidance(scheme: dict, lang: str = "en") -> dict:
    store = get_store()
    app = scheme.get("application")
    out = {"disclaimer": t(lang, "disclaimer"), "portal": None, "application_link": None,
           "application_link_note": t(lang, "no_link"), "summary": None, "citation": None}
    portal = scheme.get("portal")
    if portal:
        out["portal"] = {**portal, "note": portal["note_hi"] if lang == "hi" and portal.get("note_hi") else portal.get("note")}
    if not app:
        out["summary_note"] = t(lang, "no_application")
        return out
    p = store.passage(app["doc_id"], app["passage_id"])
    d = store.doc(app["doc_id"])
    if p and not p["flagged"]:
        out["summary"] = app["summary_hi"] if lang == "hi" and app.get("summary_hi") else app["summary"]
        out["citation"] = {"doc_id": d["id"], "passage_id": p["id"], "doc_title": d["title"], "authority": d["authority"],
                           "section": p["section"], "text": p["text"], "demo": d.get("demo", False)}
    else:
        out["summary_note"] = t(lang, "no_application")
    return out
