"""Policy-change detection between two stored versions of a scheme's official document."""
import difflib

from .eligibility import UnknownDocument, evaluate, required_display
from .i18n import t
from .sources import doc_summary
from .store import get_store, norm

IMPACT = {
    "en": {
        "lte_up": "The limit is higher, so more applicants may now qualify.",
        "lte_down": "The limit is lower, so fewer applicants may now qualify.",
        "gte_up": "The minimum is higher, so the condition is stricter.",
        "gte_down": "The minimum is lower, so the condition is more relaxed.",
        "generic": "The eligibility condition changed. Re-check it against your situation.",
        "added": "A new eligibility condition was added.",
        "removed": "An eligibility condition was removed.",
        "doc_added": "A new document is now required.",
        "doc_removed": "A document is no longer listed as required.",
        "doc_class": "The requirement level of a document changed.",
        "deadline": "The application deadline changed. Check the new date.",
        "benefit": "The benefit amount or description changed.",
        "wording": "Only the wording or formatting changed. No change to the rules was detected.",
        "section_added": "A new section was added. A person should read it to see whether it changes anything.",
        "section_removed": "A section was removed. A person should check what it covered.",
    },
    "hi": {
        "lte_up": "सीमा बढ़ी है, इसलिए अब अधिक आवेदक पात्र हो सकते हैं।",
        "lte_down": "सीमा घटी है, इसलिए अब कम आवेदक पात्र हो सकते हैं।",
        "gte_up": "न्यूनतम सीमा बढ़ी है, इसलिए शर्त अधिक कठोर है।",
        "gte_down": "न्यूनतम सीमा घटी है, इसलिए शर्त अधिक सरल है।",
        "generic": "पात्रता की शर्त बदली है। इसे अपनी स्थिति से दोबारा जाँचें।",
        "added": "पात्रता की एक नई शर्त जोड़ी गई है।",
        "removed": "पात्रता की एक शर्त हटाई गई है।",
        "doc_added": "अब एक नया दस्तावेज़ आवश्यक है।",
        "doc_removed": "एक दस्तावेज़ अब आवश्यक के रूप में सूचीबद्ध नहीं है।",
        "doc_class": "एक दस्तावेज़ की आवश्यकता का स्तर बदला है।",
        "deadline": "आवेदन की अंतिम तिथि बदली है। नई तिथि देखें।",
        "benefit": "लाभ की राशि या विवरण बदला है।",
        "wording": "केवल शब्दावली या प्रारूप बदला है। नियमों में कोई बदलाव नहीं मिला।",
        "section_added": "एक नया खंड जोड़ा गया है। यह कुछ बदलता है या नहीं, इसे किसी व्यक्ति को पढ़कर देखना चाहिए।",
        "section_removed": "एक खंड हटाया गया है। किसी व्यक्ति को जाँचना चाहिए कि उसमें क्या था।",
    },
}


def _imp(lang: str, key: str) -> str:
    return IMPACT["hi" if lang == "hi" else "en"][key]


def _ref(doc: dict, pid: str | None, store) -> dict | None:
    if not pid:
        return None
    p = store.passage(doc["id"], pid)
    return {"doc_id": doc["id"], "doc_title": doc["title"], "passage_id": pid, "section": p["section"] if p else None,
            "text": None if (not p or p["flagged"]) else p["text"], "publication_date": doc.get("publication_date"),
            "effective_date": doc.get("effective_date")}


def compare_versions(scheme: dict, old_id: str, new_id: str, lang: str = "en", profile: dict | None = None) -> dict:
    store = get_store()
    ids = {d["id"]: d for d in scheme["documents"]}
    for i in (old_id, new_id):
        if i not in ids:
            raise UnknownDocument(f"Unknown document id for this scheme: {i}")
    old, new = ids[old_id], ids[new_id]

    verified = bool(new.get("effective_date")) and new.get("status") == "current" \
        and old.get("status") == "superseded" and bool(old.get("status_evidence"))

    def rules_of(doc_id):
        return {r["criterion"]: r for r in scheme["rules"] if r["doc_id"] == doc_id and r.get("verified")}

    def reqs_of(doc_id):
        return {q["key"]: q for q in scheme.get("required_documents", []) if q["doc_id"] == doc_id and q.get("verified")}

    changes: list[dict] = []
    covered_sections: set[str] = set()

    def add(kind, label, old_val, new_val, old_ref, new_ref, impact_key, impact_text=None):
        for ref in (old_ref, new_ref):
            if ref and ref.get("section"):
                covered_sections.add(ref["section"])
        changes.append({"kind": kind, "policy_change": True, "label": label, "old_value": old_val, "new_value": new_val,
                        "old_source": old_ref, "new_source": new_ref, "impact": impact_text or _imp(lang, impact_key),
                        "verified": verified, "requires_human_verification": not verified})

    # 1. eligibility rules
    ro, rn = rules_of(old_id), rules_of(new_id)
    for crit in list(dict.fromkeys(list(ro) + list(rn))):
        a, b = ro.get(crit), rn.get(crit)
        if a and b:
            if (a["op"], a["value"]) != (b["op"], b["value"]):
                key = "generic"
                if a["op"] == b["op"] == "lte" and isinstance(a["value"], (int, float)) and isinstance(b["value"], (int, float)):
                    key = "lte_up" if b["value"] > a["value"] else "lte_down"
                elif a["op"] == b["op"] == "gte" and isinstance(a["value"], (int, float)) and isinstance(b["value"], (int, float)):
                    key = "gte_up" if b["value"] > a["value"] else "gte_down"
                label = b["label_hi"] if lang == "hi" and b.get("label_hi") else b["label"]
                add("eligibility", label, required_display(a, lang), required_display(b, lang),
                    _ref(old, a["passage_id"], store), _ref(new, b["passage_id"], store), key)
        elif b:
            label = b["label_hi"] if lang == "hi" and b.get("label_hi") else b["label"]
            add("eligibility_added", label, None, required_display(b, lang), None, _ref(new, b["passage_id"], store), "added")
        else:
            label = a["label_hi"] if lang == "hi" and a.get("label_hi") else a["label"]
            add("eligibility_removed", label, required_display(a, lang), None, _ref(old, a["passage_id"], store), None, "removed")

    # 2. required documents
    qo, qn = reqs_of(old_id), reqs_of(new_id)
    for key in list(dict.fromkeys(list(qo) + list(qn))):
        a, b = qo.get(key), qn.get(key)
        name = store.doc_name(key, lang)
        if b and not a:
            add("document_added", name, None, b["classification"], None, _ref(new, b["passage_id"], store), "doc_added")
        elif a and not b:
            add("document_removed", name, a["classification"], None, _ref(old, a["passage_id"], store), None, "doc_removed")
        elif a["classification"] != b["classification"]:
            add("document_classification", name, a["classification"], b["classification"],
                _ref(old, a["passage_id"], store), _ref(new, b["passage_id"], store), "doc_class")

    # 3. facts (deadline, benefit)
    for fact_key, impact_key in (("deadline", "deadline"), ("benefit", "benefit")):
        a, b = old["facts"].get(fact_key), new["facts"].get(fact_key)
        if (a or b) and (a or {}).get("value") != (b or {}).get("value"):
            add(fact_key, fact_key.capitalize() if lang == "en" else {"deadline": "अंतिम तिथि", "benefit": "लाभ"}[fact_key],
                a["value"] if a else None, b["value"] if b else None,
                _ref(old, a["passage_id"], store) if a else None, _ref(new, b["passage_id"], store) if b else None, impact_key)

    # 4. wording-only / structural text changes in sections not already explained above
    so = {p["section"]: p for p in old["passages"] if not p["flagged"]}
    sn = {p["section"]: p for p in new["passages"] if not p["flagged"]}
    for sec in list(dict.fromkeys(list(so) + list(sn))):
        if sec in covered_sections:
            continue
        a, b = so.get(sec), sn.get(sec)
        if a and b:
            if norm(a["text"]) != norm(b["text"]):
                ratio = round(difflib.SequenceMatcher(None, norm(a["text"]), norm(b["text"])).ratio(), 2)
                changes.append({"kind": "wording", "policy_change": False, "label": sec, "old_value": None, "new_value": None,
                                "old_source": _ref(old, a["id"], store), "new_source": _ref(new, b["id"], store),
                                "impact": _imp(lang, "wording"), "similarity": ratio,
                                "verified": True, "requires_human_verification": False})
        elif b:
            changes.append({"kind": "section_added", "policy_change": None, "label": sec, "old_value": None, "new_value": None,
                            "old_source": None, "new_source": _ref(new, b["id"], store), "impact": _imp(lang, "section_added"),
                            "verified": False, "requires_human_verification": True})
        elif a:
            changes.append({"kind": "section_removed", "policy_change": None, "label": sec, "old_value": None, "new_value": None,
                            "old_source": _ref(old, a["id"], store), "new_source": None, "impact": _imp(lang, "section_removed"),
                            "verified": False, "requires_human_verification": True})

    result = {
        "scheme_id": scheme["id"], "scheme_name": scheme["name"], "language": lang,
        "old_doc": doc_summary(old), "new_doc": doc_summary(new),
        "effective_date": new.get("effective_date") if verified else None,
        "effective_date_established": verified,
        "verified": verified,
        "status_evidence": _ref(ids[new_id], old.get("status_evidence", {}).get("passage_id"), store) if verified else None,
        "changes": changes,
        "policy_change_count": sum(1 for c in changes if c["policy_change"]),
        "needs_review_count": sum(1 for c in changes if c["requires_human_verification"]),
        "re_evaluation": None,
    }
    if not verified:
        result["verification_note"] = ("The effective date or supersession of the newer document is not established by the "
                                       "official evidence, so these changes are shown as unverified.")
    if profile is not None:
        ev_old = evaluate(scheme, profile, lang, doc_ids=[old_id])
        ev_new = evaluate(scheme, profile, lang, doc_ids=[new_id])
        result["re_evaluation"] = {
            "old_status": ev_old["status"], "old_status_label": ev_old["status_label"],
            "new_status": ev_new["status"], "new_status_label": ev_new["status_label"],
            "result_changed": ev_old["status"] != ev_new["status"],
            "applicable_version": new_id if verified else None,
            "applicable_status": ev_new["status"] if verified else None,
            "note": None if verified else "Which version applies to you cannot be determined from the evidence.",
        }
    return result


def detect_changes(scheme: dict, lang: str = "en", profile: dict | None = None) -> dict:
    """Compare consecutive versions of each scheme document line (by version number)."""
    docs = sorted(scheme["documents"], key=lambda d: (d.get("version", 0), d.get("publication_date") or ""))
    comparisons = []
    for a, b in zip(docs, docs[1:]):
        if b.get("version", 0) > a.get("version", 0):
            comparisons.append(compare_versions(scheme, a["id"], b["id"], lang, profile))
    return {"scheme_id": scheme["id"], "comparisons": comparisons,
            "note": None if comparisons else "Only one version of the document is stored for this scheme, so there is nothing to compare."}
