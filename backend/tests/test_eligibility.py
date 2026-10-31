"""AC-02, AC-03, AC-04 and test cases 1, 2, 3, 5 (evaluation part), 7, 9."""
import copy

from app import eligibility, i18n
from app.eligibility import eval_op, evaluate
from app.sources import check_source
from app.store import reload_store

from .conftest import STUDENT


def crit(result, key):
    return next(c for c in result["criteria"] if c["criterion"] == key)


# ---------------------------------------------------------------- Test case 1
def test_tc1_potentially_eligible_student_with_citations(store):
    r = evaluate(store.scheme("DEMO-STU-001"), STUDENT)
    assert r["status"] == "likely_eligible"
    assert {c["status"] for c in r["criteria"]} == {"satisfied"}
    for c in r["criteria"]:  # AC-02: every claim has at least one supporting passage
        assert c["citations"], c["criterion"]
        cite = c["citations"][0]
        assert cite["text"] and cite["evidence"].lower() in cite["text"].lower()
    assert "final decision" in r["disclaimer"]


def test_superseded_version_is_not_used_by_default(store):
    r = evaluate(store.scheme("DEMO-STU-001"), STUDENT)
    assert r["doc_ids_used"] == ["d-stu-v2"]
    assert any(w["code"] == "superseded" for w in r["warnings"])


# ---------------------------------------------------------------- Test case 2
def test_tc2_income_exceeds_threshold(store):
    r = evaluate(store.scheme("DEMO-STU-001"), {**STUDENT, "annual_income": 350000})
    inc = crit(r, "income")
    assert inc["status"] == "not_satisfied"
    assert "₹3,00,000" in inc["required_display"] and inc["citations"][0]["passage_id"] == "p2"
    assert "₹3,50,000" in inc["note"]
    assert r["status"] == "likely_ineligible"  # a confirmed mandatory criterion fails


# ---------------------------------------------------------------- Test case 3 / AC-04
def test_tc3_missing_income_is_unknown_and_asked(store):
    prof = {k: v for k, v in STUDENT.items() if k != "annual_income"}
    r = evaluate(store.scheme("DEMO-STU-001"), prof)
    assert crit(r, "income")["status"] == "unknown"
    assert r["status"] == "undetermined"
    assert any(q["attribute"] == "annual_income" for q in r["follow_up_questions"])
    assert "satisfied" not in {crit(r, "income")["status"]}


def test_empty_profile_never_claims_eligibility(store):
    for s in store.schemes.values():
        r = evaluate(s, {})
        assert r["status"] in ("undetermined", "source_unavailable"), s["id"]
        assert not r["groups"]["satisfied"], s["id"]


# ---------------------------------------------------------------- Test case 5 (evaluation against each version)
def test_tc5_threshold_change_re_evaluates_profiles(store):
    s = store.scheme("DEMO-STU-001")
    p = {**STUDENT, "annual_income": 250000}
    old = evaluate(s, p, doc_ids=["d-stu-v1"])
    new = evaluate(s, p, doc_ids=["d-stu-v2"])
    assert crit(old, "income")["status"] == "not_satisfied" and old["status"] == "likely_ineligible"
    assert crit(new, "income")["status"] == "satisfied" and new["status"] == "likely_eligible"


# ---------------------------------------------------------------- Test case 7
def test_tc7_conflicting_documents_are_flagged_not_resolved(store):
    r = evaluate(store.scheme("DEMO-CONF-001"), {"age": 30, "annual_income": 200000})
    inc = crit(r, "income")
    assert inc["status"] == "conflicting"
    assert {v["doc_id"] for v in inc["variants"]} == {"d-conf-a", "d-conf-b"}
    assert {c["doc_id"] for c in inc["citations"]} == {"d-conf-a", "d-conf-b"}
    assert all(v["publication_date"] for v in inc["variants"])
    assert r["status"] == "undetermined"  # neither document was arbitrarily chosen
    assert any(w["code"] == "conflicting_sources" for w in r["warnings"])
    assert any(w["code"] == "unclear_validity" for w in r["warnings"])
    assert "some versions" in inc["note"]  # 2 lakh meets B (2.5 lakh) but not A (1.5 lakh)


def test_conflict_note_when_value_missing(store):
    r = evaluate(store.scheme("DEMO-CONF-001"), {"age": 30})
    assert crit(r, "income")["status"] == "conflicting"
    assert "missing" in crit(r, "income")["note"]


# ---------------------------------------------------------------- Test case 9 / AC-12
def test_tc9_source_unavailable(store):
    s = store.scheme("DEMO-UNAV-001")
    r = evaluate(s, STUDENT)
    assert r["status"] == "source_unavailable" and r["criteria"] == []
    assert "could not be retrieved" in r["summary"]
    chk = check_source(store.doc("d-unav-v1"))
    assert chk["status"] == "unavailable" and chk["retry_allowed"] is True
    assert "not been verified" in chk["message"]


# ---------------------------------------------------------------- 8.6 ambiguous extraction
def test_ambiguous_clause_is_unverified_unknown(store):
    p = {"age": 70, "annual_income": 50000, "existing_benefits": []}
    r = evaluate(store.scheme("DEMO-SEN-001"), p)
    res = crit(r, "residence_years")
    assert res["status"] == "unknown" and res["verified"] is False
    assert "could not be verified" in res["note"]
    assert r["status"] == "undetermined"  # never a definitive claim


def test_rule_without_matching_evidence_is_unverified(raw_data):
    d = copy.deepcopy(raw_data)
    farm = next(s for s in d["schemes"] if s["id"] == "DEMO-FARM-001")
    next(r for r in farm["rules"] if r["id"] == "r-farm-land")["evidence"] = "text that is not in the passage"
    store = reload_store(d)
    r = evaluate(store.scheme("DEMO-FARM-001"), {"occupation": "farmer", "landholding_hectares": 1, "age": 30})
    assert crit(r, "landholding")["status"] == "unknown" and crit(r, "landholding")["verified"] is False
    assert r["status"] == "undetermined"


# ---------------------------------------------------------------- other schemes
def test_farmer_likely_eligible_and_injection_ignored(store):
    r = evaluate(store.scheme("DEMO-FARM-001"), {"occupation": "farmer", "landholding_hectares": 1.5, "age": 30})
    assert r["status"] == "likely_eligible"
    assert any(w["code"] == "injection_ignored" for w in r["warnings"])  # Test case 8 (eligibility part)
    assert any(w["code"] == "validity_not_established" for w in r["warnings"])  # AC-07


def test_state_restriction(store):
    base = {"gender": "female", "age": 30, "business_status": "planning"}
    assert evaluate(store.scheme("DEMO-WOM-001"), {**base, "state": "karnataka"})["status"] == "likely_ineligible"
    assert evaluate(store.scheme("DEMO-WOM-001"), {**base, "state": "maharashtra"})["status"] == "likely_eligible"


def test_existing_pension_excludes(store):
    p = {"age": 70, "annual_income": 50000, "existing_benefits": ["other_pension"]}
    assert crit(evaluate(store.scheme("DEMO-SEN-001"), p), "other_pension")["status"] == "not_satisfied"
    # "not answered" (None) differs from "answered: none" ([])
    assert crit(evaluate(store.scheme("DEMO-SEN-001"), {"age": 70}), "other_pension")["status"] == "unknown"


def test_skill_scheme_education_ordering(store):
    base = {"age": 22, "employment_status": "unemployed"}
    assert evaluate(store.scheme("DEMO-SKILL-001"), {**base, "education_level": "below_class_10"})["status"] == "likely_ineligible"
    assert evaluate(store.scheme("DEMO-SKILL-001"), {**base, "education_level": "postgraduate"})["status"] == "likely_eligible"


def test_student_status_derived_from_occupation(store):
    r = evaluate(store.scheme("DEMO-STU-001"), {"occupation": "student"})
    assert crit(r, "student_status")["status"] == "satisfied"


# ---------------------------------------------------------------- deterministic primitives
def test_eval_op_edges():
    assert eval_op("between", 18, [18, 45]) is True and eval_op("between", 45, [18, 45]) is True
    assert eval_op("between", 46, [18, 45]) is False and eval_op("between", None, [18, 45]) is None
    assert eval_op("lte", 200000, 200000) is True and eval_op("lte", 200001, 200000) is False
    assert eval_op("not_contains", [], "x") is True and eval_op("not_contains", None, "x") is None
    assert eval_op("gte_level", "postgraduate", "class_10") is True and eval_op("gte_level", "class_10", "class_12") is False
    assert eval_op("in", "Delhi", ["delhi"]) is True
    assert eval_op("gte", 5, None) is None


def test_indian_number_format():
    assert i18n.inr(300000) == "₹3,00,000" and i18n.inr(100000) == "₹1,00,000" and i18n.inr(1234567) == "₹12,34,567" and i18n.inr(999) == "₹999"


def test_unknown_doc_ids_rejected(store):
    import pytest
    with pytest.raises(eligibility.UnknownDocument):
        evaluate(store.scheme("DEMO-STU-001"), {}, doc_ids=["nope"])


# ---------------------------------------------------------------- Hindi
def test_hindi_output_keeps_numbers_names_and_citations(store):
    s = store.scheme("DEMO-STU-001")
    en, hi = evaluate(s, STUDENT, "en"), evaluate(s, STUDENT, "hi")
    assert hi["status"] == en["status"]  # same deterministic result
    assert "संभावित" in hi["status_label"] and "वार्षिक" in crit(hi, "income")["label"]
    assert "₹3,00,000" in crit(hi, "income")["required_display"]
    assert "Demo Merit-cum-Means Scholarship" in hi["summary"]  # official name preserved
    assert crit(hi, "income")["citations"][0]["text"] == crit(en, "income")["citations"][0]["text"]  # source text unchanged
