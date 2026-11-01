"""CivicLens API + static frontend.  Run:  uvicorn app.main:app --reload  (from the backend/ directory)."""
import hashlib
import logging
from typing import Literal, Optional

import httpx

from fastapi import APIRouter, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import agent, discovery, fields, ingest, llm, security, online
from .changes import detect_changes
from .checklist import application_guidance, build_checklist
from .config import FRONTEND_DIR, get_settings, today
from .eligibility import UnknownDocument, evaluate
from .i18n import t
from .models import AgentRunRequest, AskRequest, AssessRequest, SearchRequest, ToolCall, OnlineDiscoveryRequest
from .retrieval import get_index
from .sources import check_source, doc_flags, doc_summary
from .store import get_store

log = logging.getLogger("civiclens")
Lang = Literal["en", "hi"]

CATEGORIES = ["education", "agriculture", "entrepreneurship", "social_security", "employment", "housing", "health"]
TARGET_GROUPS = ["students", "farmers", "women", "job_seekers", "entrepreneurs", "senior_citizens", "citizens"]
SCHEME_TYPES = ["scholarship", "grant", "pension", "training", "stipend", "subsidy"]


def _err(status: int, code: str, message: str, **extra) -> JSONResponse:
    return JSONResponse(status_code=status, content={"error": code, "message": message, **extra})


def _scheme_or_404(scheme_id: str) -> dict:
    s = get_store().scheme(scheme_id)
    if not s:
        raise HTTPException(404, detail="Scheme not found in the covered sources.")
    return s


def _passage_cite(store, sid: str, doc_id: str, pid: str, section: str, text: str) -> dict:
    d = store.doc(doc_id)
    return {"scheme_id": sid, "doc_id": doc_id, "passage_id": pid, "section": section, "text": text,
            "doc_title": d["title"], "authority": d["authority"], "publication_date": d.get("publication_date"),
            "effective_date": d.get("effective_date"), "last_checked": d.get("last_checked"), "url": d.get("url"),
            "demo": d.get("demo", False), "flags": doc_flags(d)}


def build_router() -> APIRouter:
    api = APIRouter(prefix="/api")

    @api.get("/health")
    def health():
        return {"status": "ok", "schemes": len(get_store().schemes), "llm_configured": llm.is_configured()}

    @api.get("/meta")
    def meta(language: Lang = "en"):
        store = get_store()
        return {
            "fields": fields.spec_for_api(), "states": fields.STATES, "categories": CATEGORIES,
            "document_catalog": {k: {"en": v["name"], "hi": v.get("name_hi") or v["name"]} for k, v in store.catalog.items()},
            "target_groups": TARGET_GROUPS, "scheme_types": SCHEME_TYPES, "languages": [{"code": "en", "name": "English"}, {"code": "hi", "name": "हिन्दी"}],
            "data_notice": store.meta.get("data_notice_hi" if language == "hi" else "data_notice"),
            "coverage_note": store.meta.get("coverage_note"), "scheme_count": len(store.schemes),
            "llm_configured": llm.is_configured(), "privacy_notice": t(language, "privacy_notice"),
            "disclaimer": t(language, "disclaimer"), "today": today().isoformat(),
        }

    @api.get("/schemes")
    def list_schemes(language: Lang = "en", state: Optional[str] = None, category: Optional[str] = None,
                     target_group: Optional[str] = None, scheme_type: Optional[str] = None):
        from .models import Filters
        f = Filters(state=state, category=category, target_group=target_group, scheme_type=scheme_type)
        cards = [discovery.scheme_card(s, language) for s in get_store().schemes.values() if discovery._passes_filters(s, f)]
        return {"schemes": cards}

    @api.get("/schemes/{scheme_id}")
    def scheme_detail(scheme_id: str, language: Lang = "en"):
        s = _scheme_or_404(scheme_id)
        docs = []
        for d in s["documents"]:
            clean, flagged = security.split_passages(d["passages"])
            docs.append({**doc_summary(d), "retrieval_status": d.get("retrieval_status", "ok"), "passages": clean,
                         "withheld_passages": [{"id": p["id"], "reason": "instruction-like text detected"} for p in flagged],
                         "flags": doc_flags(d, language), "facts": d.get("facts", {})})
        return {"scheme": discovery.scheme_card(s, language), "documents": docs, "application": application_guidance(s, language),
                "freshness_note": t(language, "freshness_note")}

    @api.post("/schemes/{scheme_id}/eligibility")
    def scheme_eligibility(scheme_id: str, req: AssessRequest):
        return evaluate(_scheme_or_404(scheme_id), req.profile.eval_dict(), req.language, req.doc_ids)

    @api.post("/schemes/{scheme_id}/checklist")
    def scheme_checklist(scheme_id: str, req: AssessRequest):
        return build_checklist(_scheme_or_404(scheme_id), req.profile.eval_dict(), req.language, req.doc_ids)

    @api.post("/schemes/{scheme_id}/changes")
    def scheme_changes(scheme_id: str, req: AssessRequest):
        return detect_changes(_scheme_or_404(scheme_id), req.language, req.profile.eval_dict())

    @api.post("/schemes/{scheme_id}/assessment")
    def scheme_assessment(scheme_id: str, req: AssessRequest):
        """Everything the scheme detail page needs, in one call."""
        s = _scheme_or_404(scheme_id)
        p = req.profile.eval_dict()
        return {
            "scheme": discovery.scheme_card(s, req.language, p),
            "eligibility": evaluate(s, p, req.language, req.doc_ids),
            "checklist": build_checklist(s, p, req.language, req.doc_ids),
            "application": application_guidance(s, req.language),
            "changes": detect_changes(s, req.language, p),
        }

    @api.post("/search")
    def search(req: SearchRequest):
        result = agent.execute_tool("search_official_sources", req.model_dump(exclude={"online"}))
        if req.online:
            try:
                result["online_discovery"] = online.discover(req.query, req.limit)
            except Exception:  # online failures must not remove local results
                result["online_discovery"] = {"results": [], "online": True,
                                               "notice": "Online discovery was unavailable; showing local reviewed results only."}
        return result

    @api.post("/discover")
    def discover_online(req: OnlineDiscoveryRequest):
        reason = security.reject_sensitive(req.query)
        if reason: raise HTTPException(400, detail=reason)
        return online.discover(req.query, req.limit)

    @api.post("/discover/retrieve")
    def retrieve_online(lead: dict):
        """Retrieve one discovery lead. The lead is validated again; it is not trusted from the client."""
        url = lead.get("source_url") if isinstance(lead, dict) else None
        if not isinstance(url, str) or not security.is_approved_url(url):
            raise HTTPException(422, detail="A valid approved official source URL is required.")
        try:
            return online.retrieve({"source_url": url, "name": lead.get("name"), "authority": lead.get("authority")})
        except (ValueError, httpx.HTTPError) as e:
            raise HTTPException(502, detail=str(e))

    @api.post("/drafts/{scheme_id}/eligibility")
    def draft_eligibility(scheme_id: str, req: AssessRequest):
        draft = online.draft(scheme_id); store = online.draft_store(scheme_id)
        if not draft or not store: raise HTTPException(404, detail="Draft scheme not found or it has expired.")
        return evaluate(draft, req.profile.eval_dict(), req.language, req.doc_ids, store=store)

    @api.post("/agent/run")
    def agent_run(req: AgentRunRequest):
        return agent.run_agent(req)

    @api.post("/agent/tool")
    def agent_tool(call: ToolCall):
        """Allow-listed tool entry point (also used to demonstrate that unauthorised tools are rejected)."""
        return agent.execute_tool(call.tool, call.args)

    @api.post("/ask")
    def ask(req: AskRequest):
        reason = security.reject_sensitive(req.question)
        if reason:
            raise HTTPException(400, detail=reason)
        store = get_store()
        if req.scheme_id:
            _scheme_or_404(req.scheme_id)
        passages = get_index(store).retrieve_passages(req.question, req.scheme_id, k=4)
        base = {"language": req.language, "disclaimer": t(req.language, "disclaimer"), "freshness_note": t(req.language, "freshness_note")}
        if not passages:
            return {**base, "abstained": True, "answer": None, "answer_source": None, "llm_status": "not_used",
                    "message": t(req.language, "ask_abstain"), "citations": []}

        cites = [{**_passage_cite(store, p["scheme_id"], p["doc_id"], p["passage_id"], p["section"], p["text"]),
                  "score": p["score"], "key": f'{p["doc_id"]}:{p["passage_id"]}'} for p in passages]
        out = {**base, "abstained": False, "answer": None, "answer_source": "extractive", "llm_status": "not_configured",
               "message": t(req.language, "ask_extractive"), "citations": cites}
        if llm.is_configured():
            try:
                res = llm.answer_question(req.question, [{"key": c["key"], "text": c["text"], "section": c["section"]} for c in cites], req.language)
                keep = set(res["citations"])
                out.update(answer=res["answer"], answer_source="llm", llm_status="ok", message=t(req.language, "ask_llm"),
                           citations=[c for c in cites if c["key"] in keep] or cites)
            except llm.LLMUnavailable:
                out["llm_status"] = "unavailable"
            except llm.ValidationFailed:
                out["llm_status"] = "rejected_invalid_output"
        return out

    @api.post("/sources/{doc_id}/check")
    def source_check(doc_id: str, language: Lang = "en"):
        d = get_store().doc(doc_id)
        if not d:
            raise HTTPException(404, detail="Document not found.")
        return check_source(d, language)

    @api.post("/documents/inspect")
    async def inspect_document(file: UploadFile = File(...)):
        """Validate an uploaded document and report metadata only. The content is processed in memory, never stored,
        logged or returned (privacy: AC-11)."""
        s = get_settings()
        data = await file.read(s.max_upload_bytes + 1)
        kind, error = security.validate_upload(file.filename or "", file.content_type, data, s.max_upload_bytes)
        if error:
            raise HTTPException(415 if "Unsupported" in error else 400, detail=error)
        try:
            return ingest.inspect_bytes(kind, data)
        except ValueError as e:
            raise HTTPException(422, detail=str(e))

    return api


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    for noisy in ("httpx", "httpcore"):
        logging.getLogger(noisy).setLevel(logging.WARNING)  # never log outbound request URLs
    app = FastAPI(title="CivicLens", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
    limiter = security.RateLimiter(get_settings().rate_limit_per_minute)
    app.state.limiter = limiter
    max_body = get_settings().max_upload_bytes + 100_000

    @app.middleware("http")
    async def guard(request: Request, call_next):
        path = request.url.path
        if path.startswith("/api/"):
            client = request.client.host if request.client else "unknown"
            if not limiter.allow(client):
                return _err(429, "rate_limited", "Too many requests. Please wait a minute and try again.")
            cl = request.headers.get("content-length")
            limit = max_body if path == "/api/documents/inspect" else 1_000_000
            if cl and cl.isdigit() and int(cl) > limit:
                return _err(413, "payload_too_large", "The request is too large.")
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = ("default-src 'self'; img-src 'self' data:; style-src 'self'; "
                                                       "script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        if path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        # Log method, path and status only. Never bodies, queries or profiles.
        log.info("%s %s %s", request.method, path, response.status_code)
        return response

    @app.exception_handler(RequestValidationError)
    async def on_validation(request: Request, exc: RequestValidationError):
        details = [{"field": ".".join(str(x) for x in e["loc"][1:]) or str(e["loc"][0]), "message": e["msg"]} for e in exc.errors()]
        return _err(422, "validation_error", "Some inputs are not valid.", details=details)

    @app.exception_handler(HTTPException)
    async def on_http(request: Request, exc: HTTPException):
        return _err(exc.status_code, "request_error", str(exc.detail))

    @app.exception_handler(agent.ToolNotAllowed)
    async def on_tool_not_allowed(request: Request, exc: agent.ToolNotAllowed):
        return _err(403, "tool_not_allowed", "This tool is not on the agent's allowlist and was not executed.",
                    allowed_tools=sorted(agent.ALLOWED_TOOLS))

    @app.exception_handler(agent.ToolArgsInvalid)
    async def on_tool_args(request: Request, exc: agent.ToolArgsInvalid):
        return _err(422, "invalid_tool_arguments", "The tool arguments are not valid.", details=exc.errors)

    @app.exception_handler(agent.UnknownScheme)
    async def on_unknown_scheme(request: Request, exc: agent.UnknownScheme):
        return _err(404, "scheme_not_found", "Scheme not found in the covered sources.")

    @app.exception_handler(UnknownDocument)
    async def on_unknown_doc(request: Request, exc: UnknownDocument):
        return _err(404, "document_not_found", str(exc))

    @app.exception_handler(agent.SensitiveInput)
    async def on_sensitive(request: Request, exc: agent.SensitiveInput):
        return _err(400, "sensitive_input", str(exc))

    @app.exception_handler(Exception)
    async def on_error(request: Request, exc: Exception):
        log.error("unhandled %s on %s", type(exc).__name__, request.url.path)  # no stack trace, no user data
        return _err(500, "internal_error", "Something went wrong on our side. Your inputs were not stored. Please try again.")

    app.include_router(build_router())
    if FRONTEND_DIR.exists():
        app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
    return app


app = create_app()
