"""Mocked online discovery tests. No government site is contacted by this suite."""
import pytest
import httpx

from app import online


class Response:
    def __init__(self, content=b"", status_code=200, headers=None):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"content-type": "text/html"}

    def json(self):
        import json
        return json.loads(self.content.decode("utf-8"))


def test_discovery_deduplicates_official_leads(monkeypatch):
    html = b'''<html><title>Search</title><a href="https://www.myscheme.gov.in/schemes/health">Health Support Scheme</a>'''
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(html))
    monkeypatch.setattr(online, "DISCOVERY_PAGES", ("https://www.myscheme.gov.in/search",) * 2)
    result = online.discover("health support")
    assert len(result["results"]) == 1
    assert result["results"][0]["already_local"] is False
    assert "not eligibility evidence" in result["notice"]


def test_myscheme_structured_search_response_becomes_a_lead(monkeypatch):
    import json
    payload = {"data": {"hits": {"items": [{"fields": {"schemeName": "New Farmer Grant", "slug": "new-farmer-grant",
                                                               "nodalDepartmentName": "Agriculture Department",
                                                               "briefDescription": "A discovery summary."}}]}}}
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online, "DISCOVERY_PAGES", ())
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(json.dumps(payload).encode()))
    result = online.discover("farmer", 5)
    assert result["results"][0]["name"] == "New Farmer Grant"
    assert result["results"][0]["source_url"].endswith("/schemes/new-farmer-grant")
    assert result["results"][0]["description"] == "A discovery summary."
    assert result["state"] == "official_results"


def test_discovery_excludes_non_official_links(monkeypatch):
    html = b'''<a href="https://example.com/fake">Farmer Grant</a>
               <a href="https://agri.gov.in/schemes/real">Farmer Grant</a>'''
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(html))
    monkeypatch.setattr(online, "DISCOVERY_PAGES", ("https://www.gov.in/search",))
    result = online.discover("farmer grant")
    assert [x["source_url"] for x in result["results"]] == ["https://agri.gov.in/schemes/real"]


def test_discovery_reports_empty_and_source_failure_states(monkeypatch):
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online, "DISCOVERY_PAGES", ())
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b'{"data":{"hits":{"items":[]}}}'))
    empty = online.discover("does-not-exist")
    assert empty["results"] == [] and empty["state"] == "no_official_results"

    def fail(*args, **kwargs):
        raise httpx.ConnectError("offline")
    monkeypatch.setattr(online.httpx, "get", fail)
    failed = online.discover("farmer")
    assert failed["results"] == [] and failed["state"] == "source_failure"


def test_retrieval_extracts_draft_without_mutating_reviewed_store(monkeypatch, store):
    html = b"<html><title>Health Support Scheme</title><p>Annual income must not exceed Rs. 2,50,000.</p></html>"
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(html))
    result = online.retrieve({"name": "Health Support Scheme", "authority": "Ministry", "source_url": "https://www.gov.in/scheme/health"})
    assert result["retrieved"] and result["source_coverage"] == "partial"
    assert result["rules_extracted"] == 1
    draft = online.draft(result["draft_id"])
    assert draft["online_draft"] and draft["documents"][0]["manual_verification"]
    assert result["draft_id"] not in store.schemes
    assert draft["rules"][0]["evidence"] in draft["documents"][0]["passages"][0]["text"]


def test_missing_profile_is_unknown_and_partial_source_blocks_confident_result(monkeypatch):
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b"<p>Annual income must not exceed Rs. 2,50,000.</p>"))
    result = online.retrieve({"name": "Draft", "authority": "Ministry", "source_url": "https://www.gov.in/scheme/draft"})
    from app.eligibility import evaluate
    ev = evaluate(online.draft(result["draft_id"]), {}, store=online.draft_store(result["draft_id"]))
    assert ev["criteria"][0]["status"] == "unknown"
    assert ev["status"] == "undetermined"
    assert any(x["code"] == "partial_coverage" for x in ev["blockers"])


def test_oversized_source_and_private_redirect_are_rejected(monkeypatch):
    monkeypatch.setattr(online, "_safe_url", lambda url: not url.startswith("http://127."))
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b"x" * (online.MAX_RESPONSE_BYTES + 1)))
    with pytest.raises(ValueError, match="larger"):
        online.retrieve({"name": "x", "authority": "Ministry", "source_url": "https://www.gov.in/x"})

    def redirect(*a, **k):
        return Response(b"", 302, {"location": "http://127.0.0.1/admin"})
    monkeypatch.setattr(online.httpx, "get", redirect)
    with pytest.raises(ValueError, match="redirect"):
        online.retrieve({"name": "x", "authority": "Ministry", "source_url": "https://www.gov.in/x2"})


def test_invalid_url_timeout_and_unsupported_content_type_fail_safely(monkeypatch):
    with pytest.raises(ValueError, match="approved public government"):
        online.retrieve({"name": "x", "authority": "Ministry", "source_url": "http://127.0.0.1/private"})

    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: (_ for _ in ()).throw(httpx.ReadTimeout("slow")))
    with pytest.raises(httpx.ReadTimeout):
        online.retrieve({"name": "x", "authority": "Ministry", "source_url": "https://www.gov.in/slow"})

    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b"binary", headers={"content-type": "application/zip"}))
    with pytest.raises(ValueError, match="unsupported content type"):
        online.retrieve({"name": "x", "authority": "Ministry", "source_url": "https://www.gov.in/archive"})


def test_official_json_content_is_retrieved_and_extracted(monkeypatch):
    import json
    payload = {"schemeContent": "Applicants must be aged 60 years and above and annual income must not exceed Rs. 100000."}
    online._cache.clear()
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(json.dumps(payload).encode(), headers={"content-type": "application/json"}))
    result = online.retrieve({"name": "JSON Scheme", "authority": "Department", "source_url": "https://www.gov.in/api/scheme"})
    assert result["rules_extracted"] == 2
    assert {r["attribute"] for r in result["scheme"]["rules"]} == {"age", "annual_income"}


def test_empty_myscheme_detail_api_is_not_success(monkeypatch):
    monkeypatch.setenv("CIVICLENS_MYSCHEME_API_KEY", "public-test-key")
    online._cache.clear()
    online._drafts.clear()
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b"Something went wrong. Please try again later. Sign Out"))
    monkeypatch.setattr(online.httpx, "post", lambda *a, **k: Response(b'{"status":"Success","data":[]}'))
    with pytest.raises(ValueError, match="no scheme content"):
        online.retrieve({"name": "Empty Detail", "authority": "Department", "source_url": "https://www.myscheme.gov.in/schemes/empty-detail"})
    assert not online._drafts


def test_fetch_logs_http_diagnostics_without_query_string(monkeypatch, caplog):
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(b"<p>Official content</p>", headers={"content-type": "text/html"}))
    with caplog.at_level("INFO", logger="civiclens.online"):
        online.retrieve({"name": "Logged", "authority": "Department", "source_url": "https://www.gov.in/scheme/logged?secret=no"})
    record = next(r.message for r in caplog.records if "official_fetch" in r.message)
    assert "status=200" in record and "content_type=text/html" in record and "generic_error_shell=False" in record
    assert "secret" not in record


def test_pdf_content_type_is_supported_without_pdf_suffix(monkeypatch):
    from pypdf import PdfWriter
    import io
    stream = io.BytesIO(); writer = PdfWriter(); writer.add_blank_page(width=72, height=72); writer.write(stream)
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(stream.getvalue(), headers={"content-type": "application/pdf"}))
    result = online.retrieve({"name": "Guideline PDF", "authority": "Ministry", "source_url": "https://www.gov.in/document/42"})
    assert result["retrieved"] and result["scheme"]["documents"][0]["doc_type"] == "official scheme page"


def test_myscheme_error_shell_uses_official_detail_api(monkeypatch):
    monkeypatch.setenv("CIVICLENS_MYSCHEME_API_KEY", "public-test-key")
    online._cache.clear()
    shell = Response(b"Something went wrong. Please try again later.")
    detail = Response(b'{"data":[{"en":{"basicDetails":{"schemeName":"Farmer Pension Scheme"},"schemeContent":{"briefDescription":"Farmers who are above 60 years of age own up to 2 hectares of land."}}}]}', headers={"content-type": "application/json"})
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: shell)
    monkeypatch.setattr(online.httpx, "post", lambda *a, **k: detail)
    result = online.retrieve({"name": "Farmer Pension Scheme", "authority": "Department", "source_url": "https://www.myscheme.gov.in/schemes/kpy"})
    assert result["rules_extracted"] == 2
    assert result["scheme"]["documents"][0]["retrieval_source_url"].endswith("/schemes")
    assert {r["attribute"] for r in result["scheme"]["rules"]} == {"age", "landholding_hectares"}


def test_discovery_age_snippet_is_not_used_when_retrieval_is_error_shell(monkeypatch):
    lead = {"name": "Varishtha Pension Bima Yojana", "authority": "Government authority",
            "source_url": "https://www.myscheme.gov.in/schemes/vpby",
            "description": "Citizens aged 60 years and above."}
    online._cache.clear()
    online._drafts.clear()
    monkeypatch.delenv("CIVICLENS_MYSCHEME_API_KEY", raising=False)
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(
        b"Something went wrong. Please try again later. Sign Out", headers={"content-type": "text/html"}))
    with pytest.raises(ValueError, match="generic error page"):
        online.retrieve(lead)
    assert not online._drafts


def test_retrieved_age_has_source_passage_and_keeps_assessment_undetermined(monkeypatch):
    from app.eligibility import evaluate
    html = b"<p>Applicants must be citizens aged 60 years and above.</p>"
    online._cache.clear()
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(html))
    result = online.retrieve({"name": "Varishtha Pension Bima Yojana", "authority": "Government authority",
                              "source_url": "https://www.gov.in/schemes/vpby-evidence"})
    draft = online.draft(result["draft_id"])
    assert result["rules_extracted"] == 1
    rule = draft["rules"][0]
    doc = draft["documents"][0]
    assert rule["attribute"] == "age" and rule["op"] == "gte" and rule["value"] == 60
    assert rule["passage_id"] == doc["passages"][0]["id"]
    assert rule["evidence"] in doc["passages"][0]["text"]
    assert doc["url"].endswith("vpby-evidence") and doc["last_checked"]
    ev = evaluate(draft, {"age": 65}, store=online.draft_store(result["draft_id"]))
    assert ev["criteria"][0]["status"] == "satisfied"
    assert ev["status"] == "undetermined"


def test_retrieved_explicit_income_residence_category_and_landholding_are_source_linked(monkeypatch):
    html = (b"<p>Annual household income must not exceed Rs. 2,50,000. "
            b"Applicants must be residents of Uttarakhand and belong to SC. "
            b"Farmers may own up to 2 hectares of land.</p>")
    online._cache.clear()
    monkeypatch.setattr(online, "_safe_url", lambda url: True)
    monkeypatch.setattr(online.httpx, "get", lambda *a, **k: Response(html))
    result = online.retrieve({"name": "Explicit Requirements", "authority": "Department",
                              "source_url": "https://www.gov.in/schemes/explicit-requirements"})
    draft = online.draft(result["draft_id"])
    assert {r["attribute"] for r in draft["rules"]} == {"annual_income", "state", "category", "landholding_hectares"}
    assert all(r["evidence"] in draft["documents"][0]["passages"][0]["text"] for r in draft["rules"])
