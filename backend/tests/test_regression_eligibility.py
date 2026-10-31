"""Regression tests for the trust rules: evidence and criterion statuses decide the result, never keyword matches
or a count of satisfied criteria. Synthetic fixtures supply contrived cases; the shipped real data supplies realistic ones.
"""
import copy
import json

import pytest

from app import llm
from app.eligibility import evaluate
from app.report import build_report
from app.store import load_data, reload_store

from .conftest import REAL_DATA, STUDENT

PROFILE_OK = STUDENT | {"state": "delhi"}  # meets every DEMO-STU-001 criterion


def crit(ev, key):
    return next(c for c in ev["criteria"] if c["criterion"] == key)


@pytest.fixture()
def real():
    return reload_store(load_data(REAL_DATA))


def demo_scheme(raw_data, sid, **changes):
    """A modified copy of a synthetic scheme, loaded into the store."""
    data = copy.deepcopy(raw_data)
    for s in data["schemes"]:
        if s["id"] == sid:
            s.update(changes)
    return reload_store(data).scheme(sid)


# ------------------------------------------------------------ 1. OBC profile vs an SC-only mandatory requirement
def test_obc_profile_against_sc_only_requirement(real):
    ev = evaluate(real.scheme("PMS-SC"), {"category": "obc", "annual_income": 100000})
    c = crit(ev, "category")
    assert c["status"] == "not_satisfied" and c["mandatory"] and c["verified"]
    assert ev["status"] == "likely_ineligible"
    assert "SC" in c["required_display"] and c["user_value_display"] == "OBC"
    assert c["citations"] and c["evidence_type"] == "verbatim" and "does not meet" in c["explanation"]
    assert "SC students" in c["citations"][0]["text"]
    assert c["next_action_code"] == "na_c_not_satisfied"


def test_obc_profile_is_accepted_by_an_obc_scheme(real):
    ev = evaluate(real.scheme("PM-YASASVI-PMS"), {"category": "obc", "annual_income": 100000})
    assert crit(ev, "category")["status"] == "satisfied"


# ------------------------------------------------------------ 2. missing Class XII percentile
def test_missing_class12_percentile_is_unknown_never_failed_or_passed(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 100000, "existing_benefits": ["none"]})
    c = crit(ev, "class12_percentile")
    assert c["status"] == "unknown" and c["manual_check"] is True and c["verification_status"] == "not_testable_here"
    assert c["next_action_code"] == "na_c_manual"
    assert ev["status"] == "undetermined"
    assert "class12_percentile" not in {q["attribute"] for q in ev["follow_up_questions"]}  # not a field we can ask
    assert any(b["code"] == "unassessed_criteria" for b in ev["blockers"])


# ------------------------------------------------------------ 3. missing or unverified income threshold
def test_missing_income_answer_is_unknown_not_not_satisfied(real):
    for sid in ("CSSS-PMUSP", "PMS-SC", "PMS-ST", "AICTE-PRAGATI", "PM-YASASVI-PMS"):
        ev = evaluate(real.scheme(sid), {})
        c = crit(ev, "income")
        assert c["status"] == "unknown" and c["user_value"] is None, sid
        assert c["next_action_code"] == "na_c_answer"
        assert ev["status"] == "undetermined" and not ev["groups"]["not_satisfied"]
        q = next(q for q in ev["follow_up_questions"] if q["attribute"] == "annual_income")
        assert q["why"]  # the user is told why the question is asked


def test_unverified_income_threshold_never_decides(raw_data):
    s = demo_scheme(raw_data, "DEMO-STU-001")
    for r in s["rules"]:
        if r["doc_id"] == "d-stu-v2" and r["criterion"] == "income":
            r["evidence"] = "shall not exceed Rs. 9,99,999"  # quote that is NOT in the passage
    s = reload_store(_with(s)).scheme("DEMO-STU-001")
    for income in (1, 10_000_000):
        ev = evaluate(s, PROFILE_OK | {"annual_income": income})
        c = crit(ev, "income")
        assert c["status"] == "unknown" and c["verified"] is False and c["verification_status"] == "unverified"
        assert c["next_action_code"] == "na_c_unverified"
        assert ev["status"] == "undetermined"


def _with(scheme):
    data = load_data(__import__("os").environ["CIVICLENS_DATA_PATH"])
    data["schemes"] = [scheme if s["id"] == scheme["id"] else s for s in data["schemes"]]
    return data


# ------------------------------------------------------------ 4. partial source coverage
def test_partial_coverage_blocks_potentially_eligible(raw_data):
    base = evaluate(demo_scheme(raw_data, "DEMO-STU-001"), PROFILE_OK)
    assert base["status"] == "likely_eligible" and base["blockers"] == []  # control: nothing else blocks it
    ev = evaluate(demo_scheme(raw_data, "DEMO-STU-001", coverage="partial"), PROFILE_OK)
    assert ev["status"] == "undetermined" and ev["counts"]["not_satisfied"] == 0 and ev["counts"]["unknown_or_conflicting"] == 0
    assert [b["code"] for b in ev["blockers"]] == ["partial_coverage"] and ev["source_coverage"] == "partial"
    assert any(w["code"] == "partial_coverage" for w in ev["warnings"])


def test_partial_coverage_does_not_hide_a_verified_failure(raw_data):
    ev = evaluate(demo_scheme(raw_data, "DEMO-STU-001", coverage="partial"), PROFILE_OK | {"annual_income": 900000})
    assert ev["status"] == "likely_ineligible" and ev["groups"]["not_satisfied"] == ["income"]


# ------------------------------------------------------------ 5. unclear scheme validity
def test_unclear_validity_blocks_potentially_eligible(raw_data):
    for state in ("unclear", "expired"):
        ev = evaluate(demo_scheme(raw_data, "DEMO-STU-001", validity=state), PROFILE_OK)
        assert ev["status"] == "undetermined" and ev["validity"]["status"] == state and ev["validity"]["blocks_eligible"]
        assert [b["code"] for b in ev["blockers"]] == ["validity_" + state]


def test_declared_unknown_validity_blocks_but_undeclared_missing_date_only_warns(raw_data):
    assert evaluate(demo_scheme(raw_data, "DEMO-STU-001", validity="unknown"), PROFILE_OK)["status"] == "undetermined"
    farm = evaluate(demo_scheme(raw_data, "DEMO-FARM-001"), {"occupation": "farmer", "landholding_hectares": 1, "age": 30})
    assert farm["status"] == "likely_eligible" and farm["validity"]["status"] == "unknown"  # documented behaviour
    assert any(w["code"] == "validity_not_established" for w in farm["warnings"])


def test_a_document_marked_unclear_makes_validity_unclear(store):
    ev = evaluate(store.scheme("DEMO-CONF-001"), {"annual_income": 100000, "age": 30})
    assert ev["validity"]["status"] == "unclear"


# ------------------------------------------------------------ 6. conflicting official sources
def test_conflicting_sources_are_disclosed_and_block(store):
    ev = evaluate(store.scheme("DEMO-CONF-001"), {"annual_income": 200000, "age": 30})
    c = crit(ev, "income")
    assert c["status"] == "conflicting" and c["next_action_code"] == "na_c_conflicting"
    assert len(c["variants"]) == 2 and len({v["authority"] for v in c["variants"]}) == 2
    assert {x["doc_id"] for x in c["citations"]} == {"d-conf-a", "d-conf-b"}
    assert ev["status"] == "undetermined" and any(b["code"] == "conflicting_criteria" for b in ev["blockers"])
    assert any(w["code"] == "conflicting_sources" for w in ev["warnings"])


# ------------------------------------------------------------ 7. matches the search words, eligibility undetermined
def test_search_match_is_separate_from_eligibility(real, client):
    r = client.post("/api/search", json={"query": "scholarship for students", "profile": {"annual_income": 100000}}).json()
    card = next(c for c in r["results"] if c["id"] == "CSSS-PMUSP")
    assert card["relevance"] > 0 and "scholarship" in card["matched_terms"]
    assert card["eligibility_assessment"]["status"] == "undetermined"
    # the match explanation talks about words only; it never mentions eligibility counts or criteria
    joined = " ".join(card["why"]).lower()
    assert "matches your words" in joined and "criteria" not in joined and "satisfied" not in joined
    assert "not a measure of eligibility" in card["relevance_note"]
    assert card["eligibility_assessment"]["blockers"]  # and the assessment says why it is undetermined


def test_relevance_is_identical_for_eligible_and_ineligible_profiles(real, client):
    q = {"query": "scholarship for SC students post matric"}
    a = client.post("/api/search", json={**q, "profile": {"category": "sc", "annual_income": 100000}}).json()["results"]
    b = client.post("/api/search", json={**q, "profile": {"category": "general", "annual_income": 9000000}}).json()["results"]
    ra = {c["id"]: c["relevance"] for c in a}
    rb = {c["id"]: c["relevance"] for c in b}
    assert ra["PMS-SC"] == rb["PMS-SC"] == 1.0  # relevance never reacts to the profile
    assert next(c for c in b if c["id"] == "PMS-SC")["eligibility_assessment"]["status"] == "likely_ineligible"
    assert "PMS-SC" in rb  # an ineligible scheme is still shown


def test_no_profile_means_no_eligibility_claim_in_search(real, client):
    card = client.post("/api/search", json={"query": "scholarship"}).json()["results"][0]
    assert "eligibility_assessment" not in card and "preliminary_status" not in card and card["why"]


# ------------------------------------------------------------ 8. verified unmet mandatory requirement
def test_verified_unmet_mandatory_requirement_is_explained_with_evidence(real, client):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 500000})
    c = crit(ev, "income")
    assert ev["status"] == "likely_ineligible" and c["status"] == "not_satisfied"
    assert "5,00,000" in c["explanation"] and "4,50,000" in c["explanation"]
    ci = c["citations"][0]
    assert ci["passage_id"] == "p5" and "Rs. 4.5 lakh" in ci["text"] and ci["verified_quote"] and ci["url"].startswith("https://scholarships.gov.in/")
    assert ev["status_reason"].startswith("At least one mandatory criterion is not met")
    card = client.post("/api/search", json={"query": "central scholarship", "profile": {"annual_income": 500000}}).json()["results"][0]
    assert card["eligibility_assessment"]["failed"][0]["required"].startswith("at most")


def test_unmet_but_unverified_rule_never_produces_ineligible(real):
    ev = evaluate(real.scheme("PMS-ST"), {"category": "st", "annual_income": 100000, "education_level": "below_class_10"})
    assert crit(ev, "class_level")["status"] == "unknown" and ev["status"] == "undetermined"


# ------------------------------------------------------------ 9. all mandatory satisfied, evidence complete
def test_all_mandatory_satisfied_with_complete_evidence(raw_data):
    s = demo_scheme(raw_data, "DEMO-STU-001", coverage="complete", validity="confirmed")
    ev = evaluate(s, PROFILE_OK)
    assert ev["status"] == "likely_eligible" and ev["blockers"] == []
    assert ev["counts"]["not_satisfied"] == 0 and ev["counts"]["unknown_or_conflicting"] == 0
    assert ev["validity"]["status"] == "confirmed" and ev["source_coverage"] == "complete"
    for c in ev["criteria"]:
        assert c["status"] == "satisfied" and c["verified"] and c["evidence_type"] == "verbatim" and c["citations"]
        assert c["next_action_code"] == "na_c_satisfied"
    assert "preliminary" in ev["disclaimer"].lower() and "final decision" in ev["disclaimer"]


def test_validity_is_derived_confirmed_for_a_current_dated_document(store):
    assert evaluate(store.scheme("DEMO-STU-001"), PROFILE_OK)["validity"] == {"status": "confirmed", "source": "derived", "blocks_eligible": False, "note": None}


# ------------------------------------------------------------ cross-cutting
def test_no_real_scheme_can_reach_potentially_eligible(real):
    best = {"annual_income": 1, "category": "sc", "gender": "female", "existing_benefits": ["none"], "education_level": "undergraduate", "age": 20}
    for sid, s in real.schemes.items():
        for cat in ("sc", "st", "obc", "ebc_dnt"):
            assert evaluate(s, best | {"category": cat})["status"] != "likely_eligible", (sid, cat)


def test_hindi_criterion_details(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 500000}, "hi")
    c = crit(ev, "income")
    assert "आपका उत्तर" in c["next_action"] and c["verification_label"] and "4,50,000" in c["explanation"]
    assert ev["status_reason"] and all(b["message"] for b in ev["blockers"])


def test_api_exposes_the_new_fields(real, client):
    r = client.post("/api/schemes/PMS-SC/eligibility", json={"profile": {"category": "obc"}}).json()
    assert {"source_coverage", "validity", "blockers", "status_reason", "unresolved_questions"} <= set(r)
    assert {"evidence_type", "verification_label", "next_action", "explanation"} <= set(r["criteria"][0])
    assert r["unresolved_questions"] and r["validity"]["status"] == "unknown"


# ------------------------------------------------------------ prompts and report
def test_prompt_files_encode_the_trust_rules():
    ex = llm.prompt_text("extraction_agent.md")
    for needle in ("VERBATIM", "SUMMARY", "INFERRED", "UNKNOWN", "Never put a summary or paraphrase inside quotation marks",
                   "less than (<), less than or equal to (<=)", "mark source coverage as partial", "`verbatim: false`", "Do not claim word-for-word verification"):
        assert needle in ex, needle
    pl = llm.prompt_text("planner_agent.md")
    for needle in ("SEARCH RELEVANCE", "ELIGIBILITY ASSESSMENT", "Never treat missing profile data as a failed criterion",
                   "ELIGIBILITY_UNDETERMINED", "POTENTIALLY_INELIGIBLE", "Do not request Aadhaar numbers"):
        assert needle in pl, needle


def test_planner_rules_reach_the_llm_system_prompts():
    seen = []
    llm.set_backend(lambda system, user: (seen.append(system), json.dumps({"explanation": "Preliminary result."}))[1])
    llm.explain_result({"scheme": "X", "overall": "Eligibility undetermined", "criteria": []}, "en")
    assert "Separate search relevance from eligibility" in seen[0] and "Never treat missing profile data as a failed criterion" in seen[0]
    assert "JSON only" in seen[0]  # the original output contract is still there


def test_verification_report_is_honest(real):
    rep = build_report(REAL_DATA)
    assert len(rep["schemes"]) == 5
    for s in rep["schemes"]:
        assert all(d["official_domain"] for d in s["documents"]) and all(d["manual_verification_required"] for d in s["documents"])
        assert s["application_url"]["verified_scheme_specific_application_page"] is False
        assert s["coverage"] == "partial" and s["validity"] in ("unclear", "unknown") and s["unresolved"]
    csss = next(s for s in rep["schemes"] if s["id"] == "CSSS-PMUSP")
    assert csss["counts"]["rules_unverified"] == 1 and csss["counts"]["requirements_unverified"] == 2
    kinds = {s["id"]: {d["is_guideline"] for d in s["documents"]} for s in rep["schemes"]}
    assert kinds["CSSS-PMUSP"] == {True} and kinds["PM-YASASVI-PMS"] == {True} and kinds["PMS-SC"] == {False} and kinds["AICTE-PRAGATI"] == {False}


def test_source_sentences_are_not_title_cased(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {})
    shown = crit(ev, "class12_percentile")["required_display"]
    assert "80th percentile" in shown and "80Th" not in shown
    assert "Studying in India" in crit(evaluate(real.scheme("PMS-SC"), {}), "study_in_india")["required_display"]
