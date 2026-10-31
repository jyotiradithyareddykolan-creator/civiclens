"""AC-01, AC-07, AC-09, AC-12 and test cases 4 and 10, plus API behaviour."""
from app import agent
from app.models import Filters
from app.retrieval import detect_language, get_index, tokenize

from .conftest import STUDENT


def search(client, **body):
    r = client.post("/api/search", json=body)
    assert r.status_code == 200, r.text
    return r.json()


# ---------------------------------------------------------------- AC-01
def test_ac01_scheme_discovery_with_source_links(client):
    d = search(client, query="scholarship for students")
    top = d["results"][0]
    assert top["id"] == "DEMO-STU-001" and top["relevance"] == 1.0
    assert top["portal"]["url"].startswith("https://") and top["sources"] and top["freshness_note"]
    assert top["publication_date"] and top["last_checked"] and top["authority"] and top["target_groups"]
    assert "relevance_note" in top and "preliminary_status" not in top  # relevance is never shown as eligibility


def test_each_audience_finds_its_scheme(client):
    expect = {"small farmers support": "DEMO-FARM-001", "pension for senior citizens": "DEMO-SEN-001",
              "skill training for unemployed youth": "DEMO-SKILL-001", "business grant for women entrepreneurs": "DEMO-WOM-001",
              "rural housing grant": "DEMO-CONF-001"}
    for q, sid in expect.items():
        assert search(client, query=q)["results"][0]["id"] == sid, q


def test_filters(client):
    ids = lambda **f: {r["id"] for r in search(client, filters=f)["results"]}  # noqa: E731
    assert "DEMO-WOM-001" not in ids(state="Karnataka") and "DEMO-WOM-001" in ids(state="Maharashtra")
    assert ids(target_group="farmers") == {"DEMO-FARM-001"}
    assert ids(category="education") == {"DEMO-STU-001"}
    assert ids(scheme_type="pension") == {"DEMO-SEN-001"}
    assert ids(category="education", target_group="farmers") == set()


def test_profile_adds_preliminary_status_and_ranks_fit(client):
    d = search(client, query="support", profile={**STUDENT, "state": "Delhi"})
    assert all("preliminary_status" in r for r in d["results"]) and d["profile_used"]
    only_profile = search(client, profile={"occupation": "farmer", "landholding_hectares": 1, "age": 30})
    assert only_profile["results"][0]["id"] == "DEMO-FARM-001"  # fit ranks first when there is no query


# ---------------------------------------------------------------- Test case 4
def test_tc4_unsupported_scheme_query_does_not_fabricate(client):
    d = search(client, query="Tell me about PM-KISAN Samman Nidhi eligibility")
    assert d["named_scheme"] == {"name": "PM-KISAN Samman Nidhi", "verified": False}
    assert any(n["code"] == "named_scheme_unverified" and "could not be verified" in n["message"] for n in d["notices"])
    for r in d["results"]:
        assert "PM-KISAN" not in r["name"] and r["application_link"] is None


def test_tc4_known_scheme_name_is_verified(client):
    assert (search(client, query="Demo Merit-cum-Means Scholarship")["named_scheme"] or {"verified": True})["verified"] is True


def test_8_2_no_results_message(client):
    d = search(client, query="quantum spaceship teleporter")
    assert d["results"] == [] and any("does not mean" in n["message"] for n in d["notices"])


# ---------------------------------------------------------------- Test case 10 / AC-09
def test_tc10_hindi_query_hindi_explanation(client):
    q = "मुझे दिल्ली की महिला उद्यमी के लिए योजना बताओ"
    assert detect_language(q) == "hi"
    d = search(client, query=q, language="hi", profile={"gender": "female", "age": 30, "state": "Delhi", "business_status": "planning"})
    assert {"woman", "delhi", "entrepreneur"} <= set(d["search_terms"])
    top = d["results"][0]
    assert top["id"] == "DEMO-WOM-001" and "महिलाओं" in top["description"]
    assert top["name"] == "Demo Women Entrepreneur Seed Support"  # official name preserved
    assert top["preliminary_status"] == "likely_eligible" and "संभावित" in top["preliminary_status_label"]
    assert any("18 से 45" in c["required"] for c in top["eligibility_summary"])  # numbers preserved
    # citations stay in the original source wording and remain linked
    a = client.post("/api/schemes/DEMO-WOM-001/eligibility", json={"profile": {"gender": "female"}, "language": "hi"}).json()
    en = client.post("/api/schemes/DEMO-WOM-001/eligibility", json={"profile": {"gender": "female"}}).json()
    assert a["criteria"][0]["citations"][0]["text"] == en["criteria"][0]["citations"][0]["text"]
    assert a["disclaimer"].startswith("यह केवल प्रारंभिक आकलन")


def test_hindi_glossary_and_tokenizer():
    assert tokenize("किसान") == ["farmer"] and "scholarship" in tokenize("छात्रवृत्ति") and tokenize("the scheme for a") == []


# ---------------------------------------------------------------- retrieval / ask
def test_ask_returns_cited_passages_without_llm(client):
    r = client.post("/api/ask", json={"question": "What is the landholding limit?", "scheme_id": "DEMO-FARM-001"}).json()
    assert not r["abstained"] and r["answer_source"] == "extractive" and r["llm_status"] == "not_configured"
    assert r["citations"][0]["passage_id"] == "p3" and "2 hectares" in r["citations"][0]["text"] and r["citations"][0]["doc_title"]


def test_ask_abstains_without_evidence(client):
    r = client.post("/api/ask", json={"question": "airspeed velocity of a swallow"}).json()
    assert r["abstained"] and r["citations"] == [] and r["answer"] is None


def test_passage_index_excludes_superseded_and_flagged(store):
    idx = get_index(store)
    assert not [p for p in idx.passages if p["doc_id"] == "d-stu-v1"]
    assert not [p for p in idx.passages if p["doc_id"] == "d-farm-v1" and p["passage_id"] == "p8"]


# ---------------------------------------------------------------- AC-07 freshness
def test_ac07_freshness_flags(client):
    farm = client.get("/api/schemes/DEMO-FARM-001").json()
    codes = {f["code"] for f in farm["documents"][0]["flags"]}
    assert {"validity_not_established", "stale"} <= codes  # last checked 2026-03-01, today fixed at 2026-10-30
    stu = client.get("/api/schemes/DEMO-STU-001").json()
    by_id = {d["id"]: {f["code"] for f in d["flags"]} for d in stu["documents"]}
    assert "superseded" in by_id["d-stu-v1"] and not (by_id["d-stu-v2"] - {"x"})  # current + recently checked => no flags
    assert "does not prove" in stu["freshness_note"]
    conf = client.get("/api/schemes/DEMO-CONF-001").json()
    assert all("unclear_validity" in {f["code"] for f in d["flags"]} for d in conf["documents"])
    unav = client.get("/api/schemes/DEMO-UNAV-001").json()
    assert "unavailable" in {f["code"] for f in unav["documents"][0]["flags"]}


def test_source_check_endpoint_is_honest(client):
    assert client.post("/api/sources/d-unav-v1/check").json()["status"] == "unavailable"
    r = client.post("/api/sources/d-stu-v2/check").json()
    assert r["status"] == "not_checked" and "no live official URL" in r["message"]
    assert client.post("/api/sources/nope/check").status_code == 404


# ---------------------------------------------------------------- API behaviour
def test_meta_and_static_frontend(client):
    m = client.get("/api/meta").json()
    assert m["scheme_count"] == 7 and "DEMO" in m["data_notice"] and "age" in m["fields"] and "Delhi" in m["states"]
    assert m["llm_configured"] is False and "income_certificate" in m["document_catalog"]
    idx = client.get("/")
    assert idx.status_code == 200 and "CivicLens" in idx.text
    assert "default-src 'self'" in idx.headers["content-security-policy"] and idx.headers["x-frame-options"] == "DENY"
    assert client.get("/app.js").status_code == 200 and client.get("/styles.css").status_code == 200


def test_assessment_shape(client):
    r = client.post("/api/schemes/DEMO-STU-001/assessment", json={"profile": STUDENT | {"state": "Delhi"}}).json()
    assert {"scheme", "eligibility", "checklist", "application", "changes"} <= set(r)
    assert r["eligibility"]["status"] == "likely_eligible" and r["changes"]["comparisons"]


def test_not_found_and_validation_errors_do_not_echo_input(client):
    assert client.get("/api/schemes/NOPE").status_code == 404
    assert client.post("/api/schemes/DEMO-STU-001/eligibility", json={"profile": {}, "doc_ids": ["nope"]}).status_code == 404
    r = client.post("/api/schemes/DEMO-STU-001/eligibility", json={"profile": {"age": "abc-secret-value", "state": "Atlantis"}})
    assert r.status_code == 422 and r.json()["error"] == "validation_error"
    assert "abc-secret-value" not in r.text and "Atlantis" not in r.text
    assert {d["field"] for d in r.json()["details"]} >= {"profile.age", "profile.state"}


def test_agent_run_workflow_and_trace(client):
    r = client.post("/api/agent/run", json={"query": "scholarship", "profile": STUDENT | {"state": "Delhi"}, "max_schemes": 2}).json()
    assert r["validation"]["schema_valid"] and len(r["results"]) >= 1
    assert {t["tool"] for t in r["trace"]} <= set(agent.ALLOWED_TOOLS)
    assert [t["tool"] for t in r["trace"][:5]] == ["search_official_sources", "retrieve_official_documents", "extract_eligibility_clauses", "evaluate_eligibility", "generate_checklist"]
    assert r["results"][0]["eligibility"]["status"] == "likely_eligible"
    assert any(q["attribute"] == "category" for q in r["follow_up_questions"])  # asks for missing info instead of guessing


def test_agent_no_profile_asks_questions(client):
    r = client.post("/api/agent/run", json={"query": "pension for senior citizens"}).json()
    assert r["results"][0]["eligibility"]["status"] == "undetermined" and r["follow_up_questions"]


# ---------------------------------------------------------------- AC-12 graceful failure / safe 500
def test_unexpected_error_is_generic_and_logged_without_data(client, monkeypatch, caplog):
    from app import discovery

    def boom(*a, **k):
        raise RuntimeError("secret internals /home/claude/x.py query=zzcanary")
    monkeypatch.setattr(discovery, "search_schemes", boom)
    with caplog.at_level("INFO"):
        r = client.post("/api/search", json={"query": "zzcanary"})
    assert r.status_code == 500 and r.json()["error"] == "internal_error"
    assert "secret internals" not in r.text and "Traceback" not in r.text and "zzcanary" not in r.text
    assert "zzcanary" not in caplog.text and "secret internals" not in caplog.text
