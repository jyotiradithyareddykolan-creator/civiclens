"""Deterministic, evidence-linked eligibility evaluation. No LLM arithmetic: every status comes from code."""
import json

from . import fields
from .fields import LEVELS
from .i18n import fmt_value, t
from .sources import collapse_flags, doc_flags, doc_summary
from .store import get_store, norm


class UnknownDocument(ValueError):
    pass


# ---------------------------------------------------------------- primitives
def get_attr(profile: dict, attr: str | None):
    if not attr:
        return None
    v = profile.get(attr)
    if attr == "is_student" and v is None and profile.get("occupation") == "student":
        return True
    return v


def eval_op(op: str, user, required) -> bool | None:
    """Return True / False, or None when the user's value is missing or incomparable."""
    if user is None or required is None:
        return None
    try:
        if op == "lt":
            return user < required
        if op == "gt":
            return user > required
        if op == "lte":
            return user <= required
        if op == "gte":
            return user >= required
        if op == "eq":
            return norm(str(user)) == norm(str(required)) if isinstance(user, str) else user == required
        if op == "in":
            return norm(str(user)) in [norm(str(x)) for x in required]
        if op == "between":
            return required[0] <= user <= required[1]
        if op == "not_contains":
            if not isinstance(user, list):
                return None
            return norm(str(required)) not in [norm(str(x)) for x in user]
        if op == "gte_level":
            if user not in LEVELS or required not in LEVELS:
                return None
            return LEVELS.index(user) >= LEVELS.index(required)
    except TypeError:
        return None
    return None


_REQ_TXT = {
    "en": {"lt": "less than {v}", "gt": "more than {v}", "lte": "at most {v}", "gte": "at least {v}", "eq": "{v}", "in": "one of: {v}", "between": "between {lo} and {hi}",
           "not_contains": "must not include: {v}", "gte_level": "at least {v}", "unreadable": "not readable in the source copy"},
    "hi": {"lt": "{v} से कम", "gt": "{v} से अधिक", "lte": "अधिकतम {v}", "gte": "कम से कम {v}", "eq": "{v}", "in": "इनमें से एक: {v}", "between": "{lo} से {hi} के बीच",
           "not_contains": "इसमें शामिल नहीं होना चाहिए: {v}", "gte_level": "कम से कम {v}", "unreadable": "स्रोत प्रति में पढ़ने योग्य नहीं"},
}


def required_display(rule: dict, lang: str) -> str:
    txt = _REQ_TXT["hi" if lang == "hi" else "en"]
    v, attr, op = rule["value"], rule["attribute"], rule["op"]
    if v is None:
        return txt["unreadable"]
    if op == "between":
        unit = " " + ("वर्ष" if lang == "hi" else "years") if attr == "age" else ""
        return txt["between"].format(lo=v[0], hi=f"{v[1]}{unit}")
    return txt[op].format(v=fmt_value(lang, attr, v))


def _cite(rule: dict, store, lang: str) -> dict:
    d = store.doc(rule["doc_id"])
    p = store.passage(rule["doc_id"], rule["passage_id"])
    return {
        "doc_id": d["id"], "passage_id": rule["passage_id"], "doc_title": d["title"], "authority": d["authority"],
        "section": p["section"] if p else None,
        "text": None if (not p or p["flagged"]) else p["text"],
        "evidence": rule.get("evidence"), "flagged": bool(p and p["flagged"]),
        "publication_date": d.get("publication_date"), "effective_date": d.get("effective_date"),
        "last_checked": d.get("last_checked"), "url": d.get("url"), "demo": d.get("demo", False),
        "verified_quote": bool(rule.get("verified")),
        "excerpt": bool(p and p.get("excerpt")), "verbatim": (p.get("verbatim", True) if p else True), "manual_verification": bool(d.get("manual_verification")),
    }


# ---------------------------------------------------------------- document selection
def select_docs(scheme: dict, doc_ids: list[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Return (active_docs, excluded_docs). Superseded documents are excluded unless explicitly requested."""
    docs = scheme["documents"]
    if doc_ids:
        by_id = {d["id"]: d for d in docs}
        missing = [i for i in doc_ids if i not in by_id]
        if missing:
            raise UnknownDocument(f"Unknown document id(s) for this scheme: {', '.join(missing)}")
        return [by_id[i] for i in doc_ids], []
    active = [d for d in docs if d.get("status") != "superseded"]
    return active, [d for d in docs if d.get("status") == "superseded"]


def _unique_flags(flags: list[dict]) -> list[dict]:
    seen, out = set(), []
    for f in flags:
        k = (f["code"], f["doc_id"])
        if k not in seen:
            seen.add(k)
            out.append(f)
    return out


# ---------------------------------------------------------------- source-level state
def scheme_validity(scheme: dict, usable: list[dict]) -> dict:
    """Current validity of the scheme's sources: confirmed | unclear | expired | unknown.

    A scheme may DECLARE its validity (curator judgement). Independently, any active document whose status is
    'unclear' makes validity unclear. Validity only blocks a 'likely eligible' result when it is unclear/expired
    or when the curator declared it unknown; a missing effective date on its own produces a warning, not a block.
    """
    declared = scheme.get("validity")
    if any(d.get("status") == "unclear" for d in usable):
        status, source = "unclear", "derived"
    elif declared in ("confirmed", "unclear", "expired", "unknown"):
        status, source = declared, "declared"
    elif usable and all(d.get("status") == "current" and d.get("effective_date") for d in usable):
        status, source = "confirmed", "derived"
    else:
        status, source = "unknown", "derived"
    blocks = status in ("unclear", "expired") or (source == "declared" and status == "unknown")
    return {"status": status, "source": source, "blocks_eligible": blocks, "note": scheme.get("validity_note")}


def criterion_detail(c: dict, lang: str, question: str | None) -> dict:
    """Evidence type, verification wording, explanation and next action for one assessed criterion."""
    cites = c.get("citations") or []
    if not cites:
        ev_type = "none"
    elif c.get("verified") and all(x.get("verbatim", True) for x in cites):
        ev_type = "verbatim"
    else:
        ev_type = "summary"
    manual_doc = any(x.get("manual_verification") for x in cites)
    if c.get("manual_check"):
        ver, ver_key = "not_testable_here", "ver_manual"
    elif not c.get("verified"):
        ver, ver_key = "unverified", "ver_unverified"
    else:
        ver, ver_key = "quote_matches_stored_excerpt", "ver_match_manual" if manual_doc else "ver_match"
    st = c["status"]
    if st == "satisfied":
        action = "na_c_satisfied"
    elif st == "not_satisfied":
        action = "na_c_not_satisfied"
    elif st == "conflicting":
        action = "na_c_conflicting"
    elif c.get("manual_check"):
        action = "na_c_manual"
    elif not c.get("verified"):
        action = "na_c_unverified"
    elif c.get("user_value") is None and question:
        action = "na_c_answer"
    else:
        action = "na_c_check"
    return {"evidence_type": ev_type, "verification_status": ver, "verification_label": t(lang, ver_key),
            "next_action": t(lang, action, question=question or ""), "next_action_code": action}


# ---------------------------------------------------------------- evaluation
def _variants_verdict(group: list[dict], user) -> str:
    results = [eval_op(r["op"], user, r["value"]) for r in group]
    if any(x is None for x in results):
        return "verdict_unknown"
    if all(results):
        return "verdict_meets_all"
    if not any(results):
        return "verdict_fails_all"
    return "verdict_mixed"


def evaluate(scheme: dict, profile: dict, lang: str = "en", doc_ids: list[str] | None = None, store=None) -> dict:
    store = store or get_store()
    active, excluded = select_docs(scheme, doc_ids)
    usable = [d for d in active if d.get("retrieval_status", "ok") == "ok"]
    usable_ids = {d["id"] for d in usable}

    warnings: list[dict] = []
    for d in active:
        warnings.extend(doc_flags(d, lang))
    for d in excluded:
        warnings.extend(doc_flags(d, lang))

    base = {
        "scheme_id": scheme["id"], "scheme_name": scheme["name"], "language": lang,
        "docs_used": [doc_summary(d) for d in usable], "doc_ids_used": [d["id"] for d in usable],
        "disclaimer": t(lang, "disclaimer"), "freshness_note": t(lang, "freshness_note"),
        "provenance": {"criteria": "Curated from official document text; each rule's evidence quote is machine-checked against the cited passage.",
                       "statuses": "Computed by deterministic code (no LLM arithmetic).",
                       "summary_text": "Template text generated from the computed result."},
    }

    if not usable:
        warnings = _unique_flags(warnings)
        return {**base, "status": "source_unavailable", "status_label": t(lang, "overall_source_unavailable"),
                "summary": t(lang, "summary_unavailable", scheme=scheme["name"]), "criteria": [],
                "groups": {"satisfied": [], "not_satisfied": [], "unknown": [], "conflicting": []},
                "counts": {"mandatory_total": 0, "satisfied": 0, "not_satisfied": 0, "unknown_or_conflicting": 0},
                "follow_up_questions": [], "warnings": warnings,
                "source_coverage": scheme.get("coverage") or "not_declared",
                "validity": {"status": "unknown", "source": "derived", "blocks_eligible": True, "note": None},
                "blockers": [{"code": "source_unavailable", "message": t(lang, "summary_unavailable", scheme=scheme["name"])}],
                "status_reason": t(lang, "reason_source_unavailable"), "unresolved_questions": scheme.get("unresolved") or []}

    injected = sum(1 for d in usable for p in d["passages"] if p["flagged"])
    if injected:
        warnings.append({"code": "injection_ignored", "severity": "info", "doc_id": None, "message": t(lang, "warn_injection", n=injected)})

    rules = [r for r in scheme["rules"] if r["doc_id"] in usable_ids]
    order: list[str] = []
    groups: dict[str, list[dict]] = {}
    for r in rules:
        if r["criterion"] not in groups:
            groups[r["criterion"]] = []
            order.append(r["criterion"])
        groups[r["criterion"]].append(r)

    criteria, follow_ups = [], {}
    for key in order:
        group = groups[key]
        verified_rules = [r for r in group if r.get("verified")]
        first = group[0]
        attr = first["attribute"]
        user = get_attr(profile, attr)
        mandatory = any(r["mandatory"] for r in group)
        label = first["label_hi"] if lang == "hi" and first.get("label_hi") else first["label"]
        exc_rule = next((r for r in group if r.get("exception")), None)
        exception = None
        if exc_rule:
            exception = exc_rule["exception_hi"] if lang == "hi" and exc_rule.get("exception_hi") else exc_rule["exception"]

        entry = {"criterion": key, "label": label, "attribute": attr, "mandatory": mandatory,
                 "user_value": user, "user_value_display": fmt_value(lang, attr, user) if user is not None else None,
                 "exception": exception, "note": None, "variants": None}

        if not verified_rules:
            entry.update(status="unknown", required_display=required_display(first, lang),
                         citations=[_cite(r, store, lang) for r in group], verified=False,
                         note=t(lang, "note_unverified"))
        else:
            sigs = {(r["attribute"], r["op"], json.dumps(r["value"])) for r in verified_rules}
            if len(sigs) > 1:
                verdict = _variants_verdict(verified_rules, user)
                entry.update(
                    status="conflicting", verified=True,
                    required_display=" | ".join(required_display(r, lang) for r in verified_rules),
                    citations=[_cite(r, store, lang) for r in verified_rules],
                    variants=[{"doc_id": r["doc_id"], "required_display": required_display(r, lang),
                               "publication_date": store.doc(r["doc_id"]).get("publication_date"),
                               "authority": store.doc(r["doc_id"])["authority"]} for r in verified_rules],
                    note=t(lang, "note_conflict", user=entry["user_value_display"] or "-", verdict=t(lang, verdict)),
                )
            elif verified_rules[0].get("manual_check"):
                # The condition is real and sourced, but this tool has no way to test it. Never guess.
                entry.update(status="unknown", verified=True, required_display=required_display(verified_rules[0], lang),
                             citations=[_cite(r, store, lang) for r in verified_rules], manual_check=True,
                             note=t(lang, "note_manual"))
            else:
                r0 = verified_rules[0]
                res = eval_op(r0["op"], user, r0["value"])
                status = "unknown" if res is None else ("satisfied" if res else "not_satisfied")
                entry.update(status=status, verified=True, required_display=required_display(r0, lang),
                             citations=[_cite(r, store, lang) for r in verified_rules])
                if status == "not_satisfied":
                    entry["note"] = t(lang, "note_not_met", user=entry["user_value_display"], req=entry["required_display"])
                elif status == "unknown":
                    entry["note"] = t(lang, "note_needs", what=fields.label(attr, lang))
                    if attr in fields.FIELD_SPECS and attr not in follow_ups:
                        follow_ups[attr] = {"attribute": attr, "question": fields.question(attr, lang),
                                            "why": t(lang, "fu_why", what=label)}
        entry["explanation"] = (t(lang, "note_met", user=entry["user_value_display"], req=entry["required_display"])
                                if entry["status"] == "satisfied" else entry["note"])
        entry.update(criterion_detail(entry, lang, fields.question(attr, lang) if attr in fields.FIELD_SPECS else None))
        criteria.append(entry)

    mand = [c for c in criteria if c["mandatory"]]
    n_sat = sum(c["status"] == "satisfied" for c in mand)
    n_not = sum(c["status"] == "not_satisfied" for c in mand)
    n_unk = sum(c["status"] in ("unknown", "conflicting") for c in mand)
    if n_not:
        status = "likely_ineligible"
    elif n_unk:
        status = "undetermined"
    elif mand:
        status = "likely_eligible"
    else:
        status = "undetermined"
    coverage = scheme.get("coverage") or "not_declared"
    validity = scheme_validity(scheme, usable)
    blockers: list[dict] = []
    if coverage in ("partial", "unknown"):
        blockers.append({"code": "partial_coverage", "message": t(lang, "blocker_partial")})
    if validity["blocks_eligible"]:
        blockers.append({"code": "validity_" + validity["status"], "message": t(lang, "blocker_validity_" + validity["status"])})
    if n_unk:
        blockers.append({"code": "unassessed_criteria", "message": t(lang, "blocker_unknown", n=n_unk)})
    if any(c["status"] == "conflicting" for c in mand):
        blockers.append({"code": "conflicting_criteria", "message": t(lang, "blocker_conflict")})
    if status == "likely_eligible" and blockers:
        # Evidence is incomplete or its currency is unclear: never present a potentially-eligible conclusion.
        status = "undetermined"
        for b in blockers:
            if b["code"] == "partial_coverage":
                warnings.append({"code": "partial_coverage", "severity": "warning", "doc_id": None, "message": t(lang, "warn_partial")})
            elif b["code"].startswith("validity_"):
                warnings.append({"code": b["code"], "severity": "warning", "doc_id": None, "message": b["message"]})

    conflicting = [c["label"] for c in criteria if c["status"] == "conflicting"]
    if conflicting:
        warnings.append({"code": "conflicting_sources", "severity": "warning", "doc_id": None,
                         "message": t(lang, "warn_conflict", what="; ".join(conflicting))})

    status_label = t(lang, f"overall_{status}")
    return {
        **base, "status": status, "status_label": status_label,
        "summary": t(lang, "summary", scheme=scheme["name"], overall=status_label, total=len(mand), sat=n_sat, not_sat=n_not, unk=n_unk),
        "criteria": criteria,
        "groups": {s: [c["criterion"] for c in criteria if c["status"] == s]
                   for s in ("satisfied", "not_satisfied", "unknown", "conflicting")},
        "counts": {"mandatory_total": len(mand), "satisfied": n_sat, "not_satisfied": n_not, "unknown_or_conflicting": n_unk},
        "follow_up_questions": list(follow_ups.values()),
        "warnings": _dedupe_warnings(collapse_flags(warnings, lang)),
        "source_coverage": coverage, "validity": validity, "blockers": blockers,
        "status_reason": t(lang, "reason_" + status),
        "unresolved_questions": scheme.get("unresolved") or [],
    }


def _dedupe_warnings(ws: list[dict]) -> list[dict]:
    seen, out = set(), []
    for w in ws:
        k = (w["code"], w.get("doc_id"), w["message"])
        if k not in seen:
            seen.add(k)
            out.append(w)
    return out
