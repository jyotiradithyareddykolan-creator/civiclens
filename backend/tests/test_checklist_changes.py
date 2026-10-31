"""AC-05, AC-06, AC-08, and test cases 5 and 6."""
import copy
import re

from app.changes import compare_versions, detect_changes
from app.checklist import application_guidance, build_checklist
from app.eligibility import evaluate
from app.security import is_approved_url
from app.store import reload_store

from .conftest import STUDENT

FULL_DOCS_MISSING_CERT = {"income_certificate": "missing", "bonafide_certificate": "available", "marksheet": "available", "bank_account": "available"}


def item(cl, key):
    return next(i for i in cl["items"] + cl["not_applicable"] if i["key"] == key)


# ---------------------------------------------------------------- Test case 6 / AC-05
def test_tc6_missing_required_certificate(store):
    s = store.scheme("DEMO-STU-001")
    p = {**STUDENT, "category": "general", "documents": FULL_DOCS_MISSING_CERT}
    assert evaluate(s, p)["status"] == "likely_eligible"  # eligibility reflects satisfied criteria
    cl = build_checklist(s, p)
    inc = item(cl, "income_certificate")
    assert inc["user_status"] == "missing" and inc["classification"] == "mandatory"
    assert inc["instructions"] and inc["instructions"]["citation"]["passage_id"] == "p9"  # verified official instructions exist
    assert "official instructions" in inc["next_action"]
    assert item(cl, "marksheet")["user_status"] == "available"
    assert cl["counts"]["missing"] == 1


def test_no_instructions_invented_when_source_has_none(store):
    s = store.scheme("DEMO-STU-001")
    cl = build_checklist(s, {**STUDENT, "category": "sc", "documents": {"caste_certificate": "missing"}})
    cc = item(cl, "caste_certificate")
    assert cc["applies"] == "applies" and cc["user_status"] == "missing"
    assert cc["instructions"] is None and "No verified official instructions" in cc["next_action"]


def test_conditional_document_applicability(store):
    s = store.scheme("DEMO-STU-001")
    general = build_checklist(s, {**STUDENT, "category": "general"})
    assert item(general, "caste_certificate") in general["not_applicable"]
    unknown = build_checklist(s, STUDENT)  # category not answered
    cc = item(unknown, "caste_certificate")
    assert cc["applies"] == "unknown" and any(q["attribute"] == "category" for q in unknown["follow_up_questions"])


def test_default_status_is_not_confirmed(store):
    cl = build_checklist(store.scheme("DEMO-STU-001"), STUDENT)
    assert item(cl, "marksheet")["user_status"] == "not_confirmed" and "Confirm" in item(cl, "marksheet")["next_action"]


def test_checklist_flags_requirement_listed_in_only_one_conflicting_source(store):
    cl = build_checklist(store.scheme("DEMO-CONF-001"), {})
    assert item(cl, "residence_proof")["source_disagreement"]
    assert item(cl, "income_certificate")["source_disagreement"] is None


def test_checklist_tenant_vs_owner(store):
    s = store.scheme("DEMO-FARM-001")
    t = build_checklist(s, {"land_tenure": "tenant"})
    assert item(t, "tenancy_agreement")["applies"] == "applies" and item(t, "land_record") in t["not_applicable"]


def test_deadline_only_when_stated(store):
    assert build_checklist(store.scheme("DEMO-FARM-001"), {})["deadline"] is None
    wom = build_checklist(store.scheme("DEMO-WOM-001"), {})
    assert wom["deadline"]["text"] == "28 February 2027" and wom["deadline"]["passed"] is False  # today is fixed at 2026-10-30


# ---------------------------------------------------------------- AC-06
def test_no_invented_application_urls(store):
    approved = {"https://scholarships.gov.in/", "https://www.myscheme.gov.in/", "https://www.india.gov.in/"}  # spec section 5.2
    for s in store.schemes.values():
        g = application_guidance(s)
        assert g["application_link"] is None
        assert g["portal"]["url"] in approved and is_approved_url(g["portal"]["url"])
        assert "does not exist" in g["portal"]["note"]  # demo scheme is clearly not on the real portal
        assert "No scheme-specific application URL" in g["application_link_note"]
        for d in s["documents"]:
            assert d["url"] is None  # demo documents never claim an official URL


def test_application_guidance_cites_source(store):
    g = application_guidance(store.scheme("DEMO-FARM-001"))
    assert g["summary"] and g["citation"]["passage_id"] == "p7"
    assert application_guidance(store.scheme("DEMO-UNAV-001"))["summary"] is None


# ---------------------------------------------------------------- AC-08 / Test case 5
def test_ac08_changed_clause_identified_with_both_citations(store):
    s = store.scheme("DEMO-STU-001")
    cmp = compare_versions(s, "d-stu-v1", "d-stu-v2")
    inc = next(c for c in cmp["changes"] if c["kind"] == "eligibility")
    assert inc["old_value"] == "at most ₹2,00,000" and inc["new_value"] == "at most ₹3,00,000"
    assert "2,00,000" in inc["old_source"]["text"] and inc["old_source"]["doc_id"] == "d-stu-v1"
    assert "3,00,000" in inc["new_source"]["text"] and inc["new_source"]["doc_id"] == "d-stu-v2"
    assert "more applicants" in inc["impact"]
    assert cmp["verified"] is True and cmp["effective_date"] == "2025-07-01"  # established by v2 passage p10 + status evidence
    kinds = {c["kind"] for c in cmp["changes"]}
    assert {"document_added", "deadline", "benefit"} <= kinds
    assert next(c for c in cmp["changes"] if c["kind"] == "document_added")["label"].startswith("Bank account")


def test_wording_only_changes_are_not_policy_changes(store):
    cmp = compare_versions(store.scheme("DEMO-STU-001"), "d-stu-v1", "d-stu-v2")
    age = next(c for c in cmp["changes"] if c["label"] == "3.3 Age")
    assert age["kind"] == "wording" and age["policy_change"] is False
    assert cmp["policy_change_count"] < len(cmp["changes"])


def test_tc5_re_evaluation_against_verified_version(store):
    s = store.scheme("DEMO-STU-001")
    cmp = compare_versions(s, "d-stu-v1", "d-stu-v2", profile={**STUDENT, "annual_income": 250000})
    re_ = cmp["re_evaluation"]
    assert re_["old_status"] == "likely_ineligible" and re_["new_status"] == "likely_eligible"
    assert re_["result_changed"] and re_["applicable_version"] == "d-stu-v2" and re_["applicable_status"] == "likely_eligible"


def test_unverified_change_when_effective_date_unknown(raw_data):
    d = copy.deepcopy(raw_data)
    stu = next(s for s in d["schemes"] if s["id"] == "DEMO-STU-001")
    v2 = next(x for x in stu["documents"] if x["id"] == "d-stu-v2")
    v2["effective_date"], v2["status"] = None, "validity_not_established"
    v1 = next(x for x in stu["documents"] if x["id"] == "d-stu-v1")
    v1["status"] = "validity_not_established"
    v1.pop("status_evidence", None)
    store = reload_store(d)
    cmp = compare_versions(store.scheme("DEMO-STU-001"), "d-stu-v1", "d-stu-v2", profile={**STUDENT, "annual_income": 250000})
    assert cmp["verified"] is False and cmp["effective_date"] is None and cmp["effective_date_established"] is False
    assert all(c["requires_human_verification"] for c in cmp["changes"] if c["policy_change"])
    assert cmp["re_evaluation"]["applicable_version"] is None  # does not guess which version applies
    assert "cannot be determined" in cmp["re_evaluation"]["note"]


def test_pure_formatting_difference_is_not_a_change(raw_data):
    d = copy.deepcopy(raw_data)
    stu = next(s for s in d["schemes"] if s["id"] == "DEMO-STU-001")
    v2 = next(x for x in stu["documents"] if x["id"] == "d-stu-v2")
    v1 = next(x for x in stu["documents"] if x["id"] == "d-stu-v1")
    v2["passages"] = [{**p, "text": "  " + p["text"].upper().replace(" ", "  ")} if p["id"] == "p1" else p for p in v2["passages"]]
    cmp = compare_versions(reload_store(d).scheme("DEMO-STU-001"), "d-stu-v1", "d-stu-v2")
    assert not [c for c in cmp["changes"] if c["label"] == "1. Objective"]


def test_single_version_scheme_has_nothing_to_compare(store):
    r = detect_changes(store.scheme("DEMO-FARM-001"))
    assert r["comparisons"] == [] and "nothing to compare" in r["note"]


def test_parallel_circulars_are_not_treated_as_versions(store):
    assert detect_changes(store.scheme("DEMO-CONF-001"))["comparisons"] == []


def test_hindi_change_impact(store):
    cmp = compare_versions(store.scheme("DEMO-STU-001"), "d-stu-v1", "d-stu-v2", "hi")
    inc = next(c for c in cmp["changes"] if c["kind"] == "eligibility")
    assert "अधिक आवेदक" in inc["impact"] and "₹3,00,000" in inc["new_value"]
