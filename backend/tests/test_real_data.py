"""Tests against the SHIPPED real-scheme dataset (backend/data/schemes.json).

These check structure and evidence discipline, not whether the government's rules are still current:
no test here can prove that a quoted figure is up to date. Everything is offline.
"""
import json
import re

import pytest

from app.checklist import build_checklist
from app.changes import detect_changes
from app.eligibility import evaluate
from app.store import load_data, norm, reload_store

from .conftest import REAL_DATA

IDS = ["CSSS-PMUSP", "PMS-SC", "PMS-ST", "AICTE-PRAGATI", "PM-YASASVI-PMS"]


@pytest.fixture()
def real():
    return reload_store(load_data(REAL_DATA))


@pytest.fixture()
def rclient(real, client):
    return client


def crit(ev, key):
    return next(c for c in ev["criteria"] if c["criterion"] == key)


# ------------------------------------------------------------------ dataset integrity
def test_real_dataset_is_not_demo_data(real):
    assert sorted(real.schemes) == sorted(IDS)
    assert "DEMO" not in json.dumps(real.meta["data_notice"]).upper().replace("REAL-DATA", "")
    for s in real.schemes.values():
        assert not s["id"].startswith("DEMO")
        assert all(d["demo"] is False for d in s["documents"])


def test_every_document_has_official_gov_url_and_dates(real):
    for s in real.schemes.values():
        for d in s["documents"]:
            assert re.match(r"^https://[a-z0-9.-]+\.(gov|nic)\.in/", d["url"]), d["id"]
            assert d["last_checked"] == "2026-10-30" and d["authority"] and d["title"]
            assert d["manual_verification"] is True and d["reading_note"]
            assert "publication_date" in d and "effective_date" in d
            assert d["effective_date"] is None  # no effective date was stated in any text read; none is invented


def test_every_verified_item_quote_is_inside_a_verbatim_passage(real):
    """The core evidence rule: a rule/requirement is verified only if its quote is inside a quoted passage."""
    for s in real.schemes.values():
        for item in s["rules"] + s["required_documents"]:
            p = real.passage(item["doc_id"], item["passage_id"])
            assert p is not None, item["id"]
            if item["verified"]:
                assert p.get("verbatim", True) is not False and norm(item["evidence"]) in norm(p["text"]), item["id"]
            if p.get("verbatim") is False:
                assert item["verified"] is False, item["id"]  # summaries can never verify anything


def test_passages_are_marked_excerpts_and_summaries_are_labelled(real):
    for s in real.schemes.values():
        for d in s["documents"]:
            for p in d["passages"]:
                assert p["excerpt"] is True
                if p["verbatim"] is False:
                    assert "not verbatim" in p["section"]


def test_known_figures_match_the_text_that_was_read(real):
    """Spot-check the numbers that drive eligibility against the stored official quotes."""
    expect = {  # rule id -> (value, a number string that must appear in its cited passage)
        "r-csss-income": (450000, "4.5 lakh"), "r-pmssc-income-26": (250000, "2.5 lakh"), "r-pmssc-income-23": (250000, "2.5 lakh"),
        "r-pmsst-income": (250000, "2.50 lakhs"), "r-pragati-income": (800000, "8 lakh"), "r-yas-income-unemp": (250000, "2.50 lakh"),
        "r-yas-income-emp": (250000, "2.50 lakh"),
    }
    for sid, s in real.schemes.items():
        for r in s["rules"]:
            if r["id"] in expect:
                value, text = expect[r["id"]]
                assert r["value"] == value and text in real.passage(r["doc_id"], r["passage_id"])["text"], r["id"]


# ------------------------------------------------------------------ eligible-looking profile (all checkable criteria met)
def test_csss_all_checkable_criteria_met_still_undetermined(real):
    prof = {"annual_income": 300000, "existing_benefits": ["none"], "education_level": "undergraduate"}
    ev = evaluate(real.scheme("CSSS-PMUSP"), prof)
    assert crit(ev, "income")["status"] == "satisfied" and crit(ev, "no_other_scholarship")["status"] == "satisfied"
    assert ev["counts"]["not_satisfied"] == 0
    # the 80th-percentile rule cannot be tested here, and the course rule is unverified: never "likely eligible"
    assert crit(ev, "class12_percentile")["status"] == "unknown" and crit(ev, "class12_percentile")["manual_check"] is True
    assert crit(ev, "course")["status"] == "unknown" and crit(ev, "course")["verified"] is False
    assert ev["status"] == "undetermined"


def test_pragati_girl_with_income_below_limit(real):
    ev = evaluate(real.scheme("AICTE-PRAGATI"), {"gender": "female", "annual_income": 799999})
    assert crit(ev, "gender")["status"] == "satisfied" and crit(ev, "income")["status"] == "satisfied"
    assert ev["status"] == "undetermined"  # girls-per-family and admission year need a human check


def test_pragati_boundary_is_strictly_less_than(real):
    ev = evaluate(real.scheme("AICTE-PRAGATI"), {"gender": "female", "annual_income": 800000})
    assert crit(ev, "income")["status"] == "not_satisfied" and ev["status"] == "likely_ineligible"
    assert "less than" in crit(ev, "income")["required_display"]


def test_yasasvi_obc_student_within_income(real):
    ev = evaluate(real.scheme("PM-YASASVI-PMS"), {"category": "obc", "annual_income": 200000})
    assert crit(ev, "category")["status"] == "satisfied" and crit(ev, "income")["status"] == "satisfied"
    assert ev["status"] == "undetermined"
    assert any(w["code"] == "unclear_validity" for w in ev["warnings"])  # scheme period in the text has ended


# ------------------------------------------------------------------ ineligible profiles
def test_pms_sc_income_above_ceiling_is_ineligible_and_cites_both_releases(real):
    ev = evaluate(real.scheme("PMS-SC"), {"category": "sc", "annual_income": 300000})
    c = crit(ev, "income")
    assert c["status"] == "not_satisfied" and ev["status"] == "likely_ineligible"
    assert {x["doc_id"] for x in c["citations"]} == {"d-pmssc-pib-2026", "d-pmssc-pib-2023"}


def test_wrong_category_is_not_satisfied(real):
    assert evaluate(real.scheme("PMS-ST"), {"category": "sc", "annual_income": 100000})["status"] == "likely_ineligible"
    assert evaluate(real.scheme("PMS-SC"), {"category": "general", "annual_income": 100000})["status"] == "likely_ineligible"
    assert evaluate(real.scheme("PM-YASASVI-PMS"), {"category": "general", "annual_income": 100000})["status"] == "likely_ineligible"


def test_csss_income_just_above_limit(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 450001})
    assert crit(ev, "income")["status"] == "not_satisfied" and ev["status"] == "likely_ineligible"
    assert evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 450000})["criteria"][0]["status"] == "satisfied"


def test_csss_receiving_another_scholarship_is_not_satisfied(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 100000, "existing_benefits": ["other_scholarship"]})
    assert crit(ev, "no_other_scholarship")["status"] == "not_satisfied" and ev["status"] == "likely_ineligible"


# ------------------------------------------------------------------ incomplete profile
def test_empty_profile_is_undetermined_and_asks_only_askable_questions(real):
    for sid in IDS:
        ev = evaluate(real.scheme(sid), {})
        assert ev["status"] == "undetermined" and ev["counts"]["satisfied"] == 0
        asked = {q["attribute"] for q in ev["follow_up_questions"]}
        assert asked <= {"annual_income", "existing_benefits", "category", "gender", "education_level"}  # never "class12_percentile" etc.


def test_partial_profile_only_resolves_what_it_covers(real):
    ev = evaluate(real.scheme("PMS-SC"), {"category": "sc"})
    assert crit(ev, "category")["status"] == "satisfied" and crit(ev, "income")["status"] == "unknown"
    assert ev["status"] == "undetermined"


# ------------------------------------------------------------------ ambiguous / unverified
def test_pms_st_class_level_is_ambiguous_and_never_decides(real):
    s = real.scheme("PMS-ST")
    r = next(x for x in s["rules"] if x["criterion"] == "class_level")
    assert r["ambiguous"] and r["verified"] is False
    for level in ("below_class_10", "class_10", "doctorate"):
        ev = evaluate(s, {"category": "st", "annual_income": 100000, "education_level": level})
        c = crit(ev, "class_level")
        assert c["status"] == "unknown" and c["verified"] is False and "Ambiguous" in c["exception"]
        assert ev["status"] == "undetermined"


def test_summary_only_requirements_are_unverified_in_the_checklist(real):
    cl = build_checklist(real.scheme("CSSS-PMUSP"), {})
    assert {i["key"]: i["classification"] for i in cl["items"]} == {"bank_account": "unverified", "income_certificate": "unverified"}
    assert all(i["verified"] is False for i in cl["items"])


def test_schemes_without_a_document_list_do_not_invent_one(real):
    for sid in ("PMS-SC", "PMS-ST", "AICTE-PRAGATI", "PM-YASASVI-PMS"):
        cl = build_checklist(real.scheme(sid), {})
        assert cl["items"] == [] and cl["application_link"] is None


def test_partial_coverage_never_yields_likely_eligible(real):
    s = real.scheme("PMS-ST")
    # make every rule checkable to prove it is the coverage flag (not the unknowns) that holds the status back
    clone = {**s, "rules": [r for r in s["rules"] if r["criterion"] != "class_level"]}
    ev = evaluate(clone, {"category": "st", "annual_income": 100000})
    assert ev["counts"]["satisfied"] == 2 and ev["counts"]["unknown_or_conflicting"] == 0
    assert ev["status"] == "undetermined" and any(w["code"] == "partial_coverage" for w in ev["warnings"])


# ------------------------------------------------------------------ citations point at the right passage
def test_citations_resolve_to_the_exact_source_passage(real):
    prof = {"annual_income": 100000, "existing_benefits": ["none"], "category": "sc", "gender": "female", "education_level": "undergraduate"}
    for sid in IDS:
        ev = evaluate(real.scheme(sid), prof)
        for c in ev["criteria"]:
            assert c["citations"], (sid, c["criterion"])
            for ci in c["citations"]:
                p = real.passage(ci["doc_id"], ci["passage_id"])
                assert ci["text"] == p["text"] and ci["url"] == real.doc(ci["doc_id"])["url"]
                assert norm(ci["evidence"]) in norm(ci["text"])
                assert ci["manual_verification"] is True and ci["excerpt"] is True


def test_specific_citations(real):
    ev = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 1})
    ci = crit(ev, "income")["citations"][0]
    assert ci["passage_id"] == "p5" and "Rs. 4.5 lakh per annum" in ci["text"] and ci["section"].startswith("4(v)")
    ev = evaluate(real.scheme("AICTE-PRAGATI"), {"annual_income": 1})
    ci = crit(ev, "income")["citations"][0]
    assert "Rs. 8 lakh per annum" in ci["text"] and ci["publication_date"] == "2021-12-08"


def test_api_citations_over_http(rclient):
    r = rclient.post("/api/schemes/PMS-SC/eligibility", json={"profile": {"category": "sc", "annual_income": 100000}}).json()
    assert r["status"] == "undetermined"  # study-in-India cannot be checked here
    c = next(x for x in r["criteria"] if x["criterion"] == "category")
    assert [x["doc_id"] for x in c["citations"]] == ["d-pmssc-pib-2026", "d-pmssc-pib-2023"]


# ------------------------------------------------------------------ freshness / manual verification flags
def test_every_scheme_carries_manual_verification_flag(real):
    for sid in IDS:
        ev = evaluate(real.scheme(sid), {})
        assert "manual_verification_required" in {w["code"] for w in ev["warnings"]}


def test_old_press_releases_are_flagged_older(real):
    codes = lambda sid: {w["code"] for w in evaluate(real.scheme(sid), {})["warnings"]}  # noqa: E731
    assert "older_source" in codes("AICTE-PRAGATI") and "older_source" in codes("PMS-ST")
    assert "validity_not_established" in codes("CSSS-PMUSP")  # no effective date -> validity never claimed


# ------------------------------------------------------------------ policy comparison
def test_no_policy_change_is_reported_without_two_official_versions(real):
    for sid in IDS:
        ch = detect_changes(real.scheme(sid))
        assert ch["comparisons"] == [] and "nothing to compare" in ch["note"]


def test_two_press_releases_are_not_treated_as_versions_of_one_document(real, rclient):
    s = real.scheme("PMS-SC")
    assert {d["version"] for d in s["documents"]} == {1}
    r = rclient.post("/api/schemes/PMS-SC/changes", json={}).json()
    assert r["comparisons"] == []


def test_unread_newer_csss_file_is_disclosed(real):
    note = real.doc("d-csss-guidelines")["reading_note"]
    assert "07022024_updated" in note and "NOT read" in note and "NOT established" in note
    assert any("07022024_updated" in u for u in real.meta["sources_not_readable"])


# ------------------------------------------------------------------ links, privacy
def test_no_invented_application_links(real, rclient):
    for sid in IDS:
        s = real.scheme(sid)
        assert s["portal"]["url"] == "https://scholarships.gov.in/" and "no scheme-specific application" in s["portal"]["note"]
        card = rclient.get(f"/api/schemes/{sid}").json()
        assert card.get("application_link") is None


def test_profile_still_has_no_sensitive_fields(real, rclient):
    for bad in ({"aadhaar": "123412341234"}, {"religion": "x"}, {"bank_account": "123456789012"}):
        r = rclient.post("/api/schemes/PMS-SC/eligibility", json={"profile": bad})
        assert r.status_code == 422
    assert rclient.post("/api/search", json={"query": "scholarship 1234 5678 9012"}).status_code in (400, 422)


def test_search_finds_real_schemes_and_recognises_names(real, rclient):
    top = lambda q, **kw: rclient.post("/api/search", json={"query": q, **kw}).json()  # noqa: E731
    assert top("scholarship for SC students post matric")["results"][0]["id"] == "PMS-SC"
    assert top("scholarship for girls in engineering diploma")["results"][0]["id"] == "AICTE-PRAGATI"
    d = top("Tell me about AICTE Pragati Scholarship")
    assert d["named_scheme"] is None or d["named_scheme"]["verified"] is True
    assert d["results"][0]["id"] == "AICTE-PRAGATI"
    d = top("Tell me about PM-KISAN Samman Nidhi")
    assert d["named_scheme"] == {"name": "PM-KISAN Samman Nidhi", "verified": False}


def test_hindi_output_keeps_numbers_and_citations(real):
    en = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 100000})
    hi = evaluate(real.scheme("CSSS-PMUSP"), {"annual_income": 100000}, "hi")
    assert hi["criteria"][0]["citations"][0]["text"] == en["criteria"][0]["citations"][0]["text"]
    assert "4,50,000" in hi["criteria"][0]["required_display"]
    assert any(w["code"] == "manual_verification_required" and "फ़ेच" in w["message"] for w in hi["warnings"])
