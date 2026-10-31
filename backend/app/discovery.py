"""Scheme discovery: filters + BM25 relevance + preliminary eligibility. Relevance is never eligibility."""
from .checklist import application_guidance
from .eligibility import evaluate, select_docs
from .i18n import t
from .retrieval import detect_language, detect_named_scheme, get_index, tokenize
from .sources import collapse_flags, doc_flags, doc_summary
from .store import get_store


def _norm_key(v: str | None) -> str:
    return (v or "").strip().lower().replace(" ", "_").replace("-", "_")


def _passes_filters(s: dict, f) -> bool:
    if f.state and "all" not in s["states"] and f.state.strip().lower() not in s["states"]:
        return False
    if f.category and _norm_key(f.category) != _norm_key(s["category"]):
        return False
    if f.target_group and _norm_key(f.target_group) not in [_norm_key(x) for x in s["target_groups"]]:
        return False
    if f.scheme_type and _norm_key(f.scheme_type) != _norm_key(s["scheme_type"]):
        return False
    return True


def _profile_provided(p: dict) -> bool:
    return any(v not in (None, {}, [], "") for k, v in p.items() if k != "language")


def eligibility_summary(scheme: dict, lang: str) -> list[dict]:
    from .eligibility import required_display
    active, _ = select_docs(scheme)
    ids = {d["id"] for d in active if d.get("retrieval_status", "ok") == "ok"}
    seen, out = set(), []
    for r in scheme["rules"]:
        if r["doc_id"] in ids and r["criterion"] not in seen and r.get("verified"):
            seen.add(r["criterion"])
            out.append({"label": r["label_hi"] if lang == "hi" and r.get("label_hi") else r["label"],
                        "required": required_display(r, lang), "mandatory": r["mandatory"]})
    return out


def scheme_card(scheme: dict, lang: str, profile: dict | None = None) -> dict:
    """Common card fields for a scheme (spec 7.2)."""
    active, _ = select_docs(scheme)
    flags = []
    for d in active:
        flags.extend(doc_flags(d, lang))
    pub = max((d["publication_date"] for d in active if d.get("publication_date")), default=None)
    eff = max((d["effective_date"] for d in active if d.get("effective_date")), default=None)
    chk = max((d["last_checked"] for d in active if d.get("last_checked")), default=None)
    card = {
        "id": scheme["id"], "name": scheme["name"], "authority": scheme["authority"],
        "target_groups": scheme["target_groups"], "category": scheme["category"], "scheme_type": scheme["scheme_type"],
        "description": scheme["description_hi"] if lang == "hi" and scheme.get("description_hi") else scheme["description"],
        "geography": scheme["geography"], "states": scheme["states"],
        "eligibility_summary": eligibility_summary(scheme, lang),
        "sources": [doc_summary(d) for d in active],
        "portal": application_guidance(scheme, lang)["portal"],
        "application_link": None, "application_link_note": t(lang, "no_link"),
        "publication_date": pub, "effective_date": eff, "last_checked": chk,
        "flags": collapse_flags(flags, lang), "freshness_note": t(lang, "freshness_note"),
        "demo": any(d.get("demo") for d in scheme["documents"]),
    }
    if profile is not None:
        ev = evaluate(scheme, profile, lang)
        card.update(preliminary_status=ev["status"], preliminary_status_label=ev["status_label"], counts=ev["counts"],
                    follow_up_questions=ev["follow_up_questions"],
                    eligibility_assessment={"status": ev["status"], "status_label": ev["status_label"], "reason": ev["status_reason"],
                                            "counts": ev["counts"], "blockers": ev["blockers"], "source_coverage": ev["source_coverage"],
                                            "validity": ev["validity"]["status"],
                                            "failed": [{"label": c["label"], "required": c["required_display"], "yours": c["user_value_display"]}
                                                       for c in ev["criteria"] if c["status"] == "not_satisfied" and c["mandatory"]]})
    return card


FIT = {"likely_eligible": 1.0, "undetermined": 0.5, "likely_ineligible": 0.0, "source_unavailable": 0.0}


def search_schemes(query: str, filters, profile: dict | None, lang: str = "en", limit: int = 10) -> dict:
    store = get_store()
    index = get_index(store)
    detected = detect_language(query)
    tokens = tokenize(query)
    notices = []

    named = detect_named_scheme(query, store) if query else None
    if named and not named["verified"]:
        notices.append({"code": "named_scheme_unverified", "message": t(lang, "named_unverified", name=named["name"])})

    have_profile = profile is not None and _profile_provided(profile)
    candidates = [s for s in store.schemes.values() if _passes_filters(s, filters)]
    scores = index.search_schemes(tokens) if tokens else {}
    max_score = max((scores[s["id"]][0] for s in candidates if s["id"] in scores), default=0.0)

    rows = []
    for s in candidates:
        sc, matched = scores.get(s["id"], (0.0, []))
        if tokens and sc <= 0:
            continue
        card = scheme_card(s, lang, profile if profile is not None else {})
        rel = (sc / max_score) if (tokens and max_score) else 0.0
        fit = FIT.get(card["preliminary_status"], 0.0) if have_profile else 0.0
        why = []
        if matched:
            why.append(("Matches your words: " if lang == "en" else "आपके शब्दों से मेल: ") + ", ".join(matched))
        if profile and profile.get("state") and "all" not in s["states"]:
            if profile["state"] in s["states"]:
                why.append("Available in your state." if lang == "en" else "आपके राज्य में उपलब्ध।")
        # `why` explains ONLY why the scheme matched the search (words, state). Eligibility lives in
        # `eligibility_assessment`; the two are shown separately and never merged.
        card.update(relevance=round(rel, 3), why=[w for w in why if w], matched_terms=matched,
                    relevance_note=("Relevance shows how well the scheme text matches your words. It is not a measure of eligibility."
                                    if lang == "en" else "प्रासंगिकता बताती है कि योजना का पाठ आपके शब्दों से कितना मेल खाता है। यह पात्रता का माप नहीं है।"))
        if not have_profile:
            card.pop("preliminary_status", None)
            card.pop("preliminary_status_label", None)
            card.pop("counts", None)
            card.pop("follow_up_questions", None)
            card.pop("eligibility_assessment", None)
        rows.append((rel + 0.25 * fit, card))

    rows.sort(key=lambda x: (-x[0], x[1]["name"]))
    results = [c for _, c in rows][:limit]
    if not results:
        notices.append({"code": "no_results", "message": t(lang, "no_results")})
    return {"results": results, "notices": notices, "named_scheme": named, "detected_language": detected,
            "search_terms": tokens, "total_considered": len(candidates), "profile_used": have_profile,
            "data_notice": store.meta.get("data_notice_hi" if lang == "hi" else "data_notice")}
