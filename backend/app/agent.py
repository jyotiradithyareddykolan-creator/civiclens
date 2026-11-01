"""Safe agent workflow: an explicit tool allowlist with validated arguments.

The agent can only search, retrieve, extract, evaluate, build checklists, compare versions and explain.
It cannot submit applications, make payments, modify records or call anything outside ALLOWED_TOOLS.
"""
from typing import Callable, Optional

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from . import discovery, llm, security, online
from .changes import compare_versions
from .checklist import build_checklist
from .eligibility import evaluate, required_display
from .models import AgentRunRequest, Filters, Profile
from .sources import doc_flags, doc_summary
from .store import get_store

ID_PATTERN = r"^[A-Za-z0-9_-]{1,60}$"


class ToolNotAllowed(Exception):
    pass


class ToolArgsInvalid(Exception):
    def __init__(self, errors):
        super().__init__("invalid tool arguments")
        self.errors = errors


class UnknownScheme(Exception):
    pass


class SensitiveInput(ValueError):
    pass


class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SearchArgs(_Args):
    query: str = Field("", max_length=500)
    filters: Filters = Field(default_factory=Filters)
    profile: Optional[Profile] = None
    language: str = Field("en", pattern=r"^(en|hi)$")
    limit: int = Field(10, ge=1, le=20)


class SchemeArgs(_Args):
    scheme_id: str = Field(..., pattern=ID_PATTERN)


class ExtractArgs(SchemeArgs):
    doc_id: Optional[str] = Field(None, pattern=ID_PATTERN)
    language: str = Field("en", pattern=r"^(en|hi)$")


class ProfileArgs(SchemeArgs):
    profile: Profile = Field(default_factory=Profile)
    language: str = Field("en", pattern=r"^(en|hi)$")
    doc_ids: Optional[list[str]] = Field(None, max_length=10)


class CompareArgs(SchemeArgs):
    old_doc_id: str = Field(..., pattern=ID_PATTERN)
    new_doc_id: str = Field(..., pattern=ID_PATTERN)
    language: str = Field("en", pattern=r"^(en|hi)$")
    profile: Optional[Profile] = None


class ExplainArgs(SchemeArgs):
    profile: Profile = Field(default_factory=Profile)
    language: str = Field("en", pattern=r"^(en|hi)$")


def _scheme(scheme_id: str) -> dict:
    s = get_store().scheme(scheme_id)
    if not s:
        raise UnknownScheme(scheme_id)
    return s


# ---------------------------------------------------------------- tools
def t_search(a: SearchArgs) -> dict:
    reason = security.reject_sensitive(a.query)
    if reason:
        raise SensitiveInput(reason)
    prof = a.profile.eval_dict() if a.profile else None
    return discovery.search_schemes(a.query, a.filters, prof, a.language, a.limit)


def t_retrieve(a: SchemeArgs) -> dict:
    s = _scheme(a.scheme_id)
    docs = []
    for d in s["documents"]:
        clean, flagged = security.split_passages(d["passages"])
        docs.append({**doc_summary(d), "retrieval_status": d.get("retrieval_status", "ok"), "passages": clean,
                     "withheld_passages": [{"id": p["id"], "reason": "instruction-like text detected", "flags": p["flags"]} for p in flagged],
                     "flags": doc_flags(d)})
    return {"scheme_id": s["id"], "documents": docs}


def t_extract(a: ExtractArgs) -> dict:
    s = _scheme(a.scheme_id)
    store = get_store()
    rules = []
    for r in s["rules"]:
        if a.doc_id and r["doc_id"] != a.doc_id:
            continue
        p = store.passage(r["doc_id"], r["passage_id"])
        rules.append({"id": r["id"], "criterion": r["criterion"], "doc_id": r["doc_id"], "passage_id": r["passage_id"],
                      "label": r["label"], "required": required_display(r, a.language), "mandatory": r["mandatory"],
                      "evidence": r["evidence"], "verified_against_passage": r["verified"],
                      "passage_text": None if (not p or p["flagged"]) else p["text"]})
    return {"scheme_id": s["id"], "clauses": rules}


def t_eval(a: ProfileArgs) -> dict:
    return evaluate(_scheme(a.scheme_id), a.profile.eval_dict(), a.language, a.doc_ids)


def t_checklist(a: ProfileArgs) -> dict:
    return build_checklist(_scheme(a.scheme_id), a.profile.eval_dict(), a.language, a.doc_ids)


def t_compare(a: CompareArgs) -> dict:
    return compare_versions(_scheme(a.scheme_id), a.old_doc_id, a.new_doc_id, a.language,
                            a.profile.eval_dict() if a.profile else None)


def t_explain(a: ExplainArgs) -> dict:
    ev = evaluate(_scheme(a.scheme_id), a.profile.eval_dict(), a.language)
    out = {"scheme_id": ev["scheme_id"], "summary": ev["summary"], "status": ev["status"], "status_label": ev["status_label"],
           "disclaimer": ev["disclaimer"], "llm_status": "not_configured", "llm_explanation": None,
           "citations": [{"criterion": c["criterion"], "status": c["status"],
                          "sources": [{"doc_id": x["doc_id"], "passage_id": x["passage_id"], "section": x["section"]} for x in c["citations"]]}
                         for c in ev["criteria"]]}
    if llm.is_configured() and ev["criteria"]:
        compact = {"scheme": ev["scheme_name"], "overall": ev["status_label"],
                   "criteria": [{"label": c["label"], "required": c["required_display"], "yours": c["user_value_display"], "status": c["status"]}
                                for c in ev["criteria"]]}
        try:
            out["llm_explanation"] = llm.explain_result(compact, a.language)["explanation"]
            out["llm_status"] = "ok"
        except llm.LLMUnavailable:
            out["llm_status"] = "unavailable"
        except llm.ValidationFailed:
            out["llm_status"] = "rejected_invalid_output"
    return out


ALLOWED_TOOLS: dict[str, tuple[type[BaseModel], Callable]] = {
    "search_official_sources": (SearchArgs, t_search),
    "retrieve_official_documents": (SchemeArgs, t_retrieve),
    "extract_eligibility_clauses": (ExtractArgs, t_extract),
    "evaluate_eligibility": (ProfileArgs, t_eval),
    "generate_checklist": (ProfileArgs, t_checklist),
    "compare_document_versions": (CompareArgs, t_compare),
    "produce_cited_explanation": (ExplainArgs, t_explain),
}


def execute_tool(name: str, args: dict) -> dict:
    """The single entry point for tool use. Unknown tools and malformed arguments are rejected."""
    if name not in ALLOWED_TOOLS:
        raise ToolNotAllowed(name)
    model, fn = ALLOWED_TOOLS[name]
    try:
        parsed = model.model_validate(args)
    except ValidationError as e:
        raise ToolArgsInvalid([{"field": ".".join(str(x) for x in err["loc"]), "message": err["msg"]} for err in e.errors()]) from None
    return fn(parsed)


# ---------------------------------------------------------------- orchestrated workflow
class AgentResult(BaseModel):
    model_config = ConfigDict(extra="allow")
    scheme_id: str
    eligibility: dict
    checklist: dict


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    results: list[AgentResult]
    follow_up_questions: list[dict]
    trace: list[dict]
    notices: list[dict]


def run_agent(req: AgentRunRequest) -> dict:
    trace: list[dict] = []
    profile = req.profile.model_dump() if req.profile else None

    def step(tool: str, args: dict, summary_fn=lambda r: ""):
        res = execute_tool(tool, args)
        trace.append({"step": len(trace) + 1, "tool": tool, "ok": True, "detail": summary_fn(res)})
        return res

    search = step("search_official_sources",
                  {"query": req.query, "filters": req.filters.model_dump(), "profile": profile, "language": req.language, "limit": req.max_schemes},
                  lambda r: f"{len(r['results'])} candidate scheme(s)")

    results, questions = [], {}
    for card in search["results"]:
        sid = card["id"]
        pa = {"scheme_id": sid, "profile": profile or {}, "language": req.language}
        docs = step("retrieve_official_documents", {"scheme_id": sid}, lambda r: f"{len(r['documents'])} document(s) for {sid}")
        step("extract_eligibility_clauses", {"scheme_id": sid, "language": req.language}, lambda r: f"{len(r['clauses'])} clause(s) for {sid}")
        ev = step("evaluate_eligibility", pa, lambda r: f"{sid}: {r['status']}")
        cl = step("generate_checklist", pa, lambda r: f"{sid}: {len(r['items'])} document item(s)")
        for q in ev["follow_up_questions"] + cl["follow_up_questions"]:
            questions.setdefault(q["attribute"], q)
        results.append({"scheme_id": sid, "card": card, "eligibility": ev, "checklist": cl,
                        "withheld_passages": sum(len(d["withheld_passages"]) for d in docs["documents"])})

    response = {
        "query": req.query, "language": req.language, "results": results,
        "follow_up_questions": list(questions.values())[:6], "trace": trace, "notices": search["notices"],
        "named_scheme": search.get("named_scheme"), "data_notice": search.get("data_notice"),
        "validation": {"schema_valid": True, "statuses_computed_by_code": True,
                       "note": "Responses are validated against a schema; eligibility statuses come from deterministic code, not from an LLM."},
    }
    if req.online:
        try:
            response["online_discovery"] = online.discover(req.query, req.max_schemes)
        except Exception:
            response["online_discovery"] = {"results": [], "online": True,
                                             "notice": "Online discovery was unavailable; showing local reviewed results only."}
    AgentResponse.model_validate(response)  # raises if the structure is wrong
    return response
