# CivicLens — Government Scheme Intelligence Agent

CivicLens helps people find government schemes they may qualify for, understand why, see which documents they need, and check the official evidence behind every claim. It combines retrieval over official documents, **deterministic** eligibility rules, a safe agent workflow with a tool allowlist, a personalised document checklist, policy-change comparison, and English/Hindi support.

> **Read this first: what the bundled data is, and is not.**
> `backend/data/schemes.json` holds **5 real student-scholarship schemes** of the Government of India. Their details were read from official government pages on **2026-10-30** through an automated fetch tool. That tool returns model-processed text, **not a byte-exact copy**, so:
> * only text the tool returned *inside quotation marks* is stored as a quotation; anything it only summarised is stored as a **summary** and can never verify a rule;
> * every document is marked **"manual verification required"**: someone must compare the exact wording with the official source before the data is relied on;
> * some documents were read only in part, and three of the five sources are **press releases** (PIB), not scheme guidelines. These schemes are marked *partial coverage*, so CivicLens **never shows "likely eligible"** for them;
> * several official files could not be read at all (their sites refuse automated access). They are listed in `meta.sources_not_readable`.
>
> The earlier synthetic demo schemes now live only in `backend/tests/fixtures/demo_schemes.json` and are used by the engine tests.

Results are **preliminary assessments**. The final decision always rests with the responsible authority. CivicLens is independent and not affiliated with any government body.

---

## 1. Quick start

**Prerequisites:** Python 3.11+ (tested on 3.13). Node 18+ is only needed for the optional UI checks. No database, no build step, no API key required.

```bash
cd civiclens/backend
python3 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000**. The same server serves the API (`/api/...`, docs at `/api/docs`) and the frontend.

**Try it**

1. Click **My details** and enter, for example: category SC, annual household income 200000. Save.
2. Search *"scholarship for SC students"*. Open **Post-Matric Scholarship for Scheduled Caste students (PMS-SC)**.
3. **Eligibility** shows each criterion as satisfied / not satisfied / unknown. Income and category are checked; "studying in India" is shown as *cannot be checked by this tool*.
4. **Evidence** shows each quoted passage, the PIB link, the date, the "How this source was read" note, and the manual-verification warning.
5. **Policy changes** says there is nothing to compare, because only one official version is stored. CivicLens does not call anything an official policy change without two official versions and evidence of which applies.
6. Switch to **हिन्दी**: numbers, scheme names and the quoted source text stay unchanged.

## 2. Configuration

Copy `.env.example` to `.env` (or export the variables). **Names only; never commit real secrets.** The app reads the environment at run time; it does not load `.env` by itself, so export the variables (or use `set -a; source .env; set +a`).

| Variable | Default | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | empty | Optional. Enables AI-written answers in *Ask a question* and a plain-language explanation tool. **Without it the app runs fully in extractive/demo mode.** Server-side only; never sent to the browser. |
| `CIVICLENS_LLM_MODEL` | `claude-sonnet-5-5` | Model used when a key is set. |
| `CIVICLENS_DATA_PATH` | `backend/data/schemes.json` | Scheme dataset. |
| `CIVICLENS_LIVE_FETCH` | `0` | `1` lets "Check source now" fetch **https `*.gov.in` / `*.nic.in`** URLs only (timeout 10 s, 3 bounded retries). |
| `CIVICLENS_STALE_DAYS` | `90` | "Last checked" older than this is flagged stale. |
| `CIVICLENS_RATE_LIMIT_PER_MINUTE` | `120` | Per-IP limit on `/api/*`. |
| `CIVICLENS_MAX_UPLOAD_BYTES` | `2000000` | Upload size limit for `/api/documents/inspect`. |
| `CIVICLENS_TODAY` | empty | Fix "today" (YYYY-MM-DD) for reproducible demos/tests. |

**What the LLM does and does not do.** It never decides eligibility. Statuses, thresholds and dates come from code. When enabled it may (a) answer a question using *only* retrieved, injection-screened passages, wrapped as untrusted data, and (b) rephrase an already-computed result. Every output is checked against a strict schema: citations must be passages that were actually retrieved, numbers must appear in the source, and over-claiming language ("you are eligible", "guaranteed") is rejected. On any failure the app falls back to the extractive result and says so.

## 3. Tests

```bash
cd civiclens/backend
python -m pytest                      # 124 tests, offline, no API key
```

Test data: the engine tests (AC-01..12, test cases 1–10) run on the **synthetic fixture** because they need contrived cases (conflicting circulars, injection text, two versions). `tests/test_real_data.py` (31 tests) runs on the shipped real data: eligible-looking, ineligible, incomplete and ambiguous profiles, citation-to-passage checks, summary-vs-quote discipline, freshness flags, "no policy change without two versions", and privacy.

Optional UI checks (drive the real `index.html` + `app.js` in jsdom against a running server):

```bash
# real data (15 checks: banner, warnings, evidence tab, Hindi):
#   terminal 1: uvicorn app.main:app --port 8000              (from backend/)
cd civiclens/ui-tests && npm install && npm run test:ui:real
# demo fixture (full feature tour incl. conflict/injection/unavailable cases):
#   terminal 1: CIVICLENS_DATA_PATH=tests/fixtures/demo_schemes.json uvicorn app.main:app --port 8000
npm run test:ui
```

### Acceptance criteria → where they are checked

| Spec item | Verified by |
|---|---|
| AC-01 Scheme discovery with source links | `test_search_api.py::test_ac01_*`, `test_each_audience_finds_its_scheme`, `test_filters` |
| AC-02 Evidence for every claim | `test_eligibility.py::test_tc1_*` (every criterion has a citation whose evidence quote is inside the passage) |
| AC-03 Correct evaluation | `test_eligibility.py` (TC1, TC2, state, pension, education ordering, `eval_op` edge cases) |
| AC-04 Missing information | `test_tc3_*`, `test_empty_profile_never_claims_eligibility` |
| AC-05 Checklist | `test_checklist_changes.py::test_tc6_*`, conditional/default/tenant tests |
| AC-06 No invented links | `test_no_invented_application_urls`, `test_live_fetch_blocks_unapproved_urls`, `test_approved_domain_policy` |
| AC-07 Freshness | `test_ac07_freshness_flags` (stale, unestablished, unclear, superseded, unavailable) |
| AC-08 Change detection | `test_ac08_*`, `test_tc5_*`, unverified and wording-only tests |
| AC-09 Regional language | `test_tc10_*`, `test_hindi_*` |
| AC-10 Validation / unauthorised tools / malformed AI | `test_unauthorised_tools_are_rejected`, `test_tool_arguments_are_validated`, `test_answer_validation_rejects`, upload tests |
| AC-11 Privacy | `test_upload_content_is_not_returned_or_logged`, `test_requests_are_not_logged_with_user_data`, `test_api_key_never_exposed` |
| AC-12 Graceful failure | `test_tc9_*`, `test_llm_unavailable_*`, `test_unexpected_error_is_generic_*` |
| Test cases 1–10 | TC1/2/3/5/7/9 in `test_eligibility.py`; TC4/10 in `test_search_api.py`; TC6 in `test_checklist_changes.py`; TC8 in `test_security_llm.py` |

## 4. How it works

```
question + profile
   │
   ▼  search_official_sources   BM25 over scheme text + clean passages (Hindi → English glossary)
   ▼  retrieve_official_documents   passages with metadata; instruction-like passages withheld
   ▼  extract_eligibility_clauses   curated rules, each with a verbatim evidence quote
   ▼  evaluate_eligibility          deterministic code → satisfied / not satisfied / unknown / conflicting
   ▼  generate_checklist            documents from the source; availability from the user
   ▼  (optional) LLM wording        schema-validated, never changes a status
   ▼  response schema validation → UI
```

Key design decisions:

* **Deterministic eligibility.** `eligibility.py` applies explicit operators (`lte`, `gte`, `between`, `in`, `eq`, `not_contains`, `gte_level`) to profile values. Missing value → `unknown`, never a guess. Overall: any confirmed mandatory failure → *likely ineligible*; else any mandatory unknown/conflicting → *undetermined*; else *likely eligible*.
* **Grounding check.** At load time every rule's `evidence` string must appear verbatim in the passage it cites, in a passage that was not flagged. If not, the rule is *unverified* and evaluates to `unknown`.
* **Conflicts are shown, not resolved.** If non-superseded documents disagree on a criterion, the criterion is `conflicting`, both sources are cited with dates and authorities, and no document is assumed authoritative. A document is only treated as superseded when the data records evidence (a passage) for that.
* **Freshness ≠ validity.** "Last checked" is shown with a standing note that it does not prove the policy is current. Missing effective date, unclear supersession, staleness and unavailability each raise a flag.
* **Untrusted text.** Passages are screened for instruction-like patterns. Flagged passages are excluded from the search index, the LLM context, extraction and the UI (the UI shows "passage withheld"). The frontend renders everything with `textContent`.
* **Tool allowlist.** `agent.ALLOWED_TOOLS` has seven read-only tools with pydantic-validated arguments (`extra="forbid"`). There is no tool to submit, pay or modify records; anything else returns 403.
* **Privacy by design.** The profile model has no field for Aadhaar, bank numbers or passwords and rejects extra fields; long digit strings are rejected in free text. The profile lives only in the browser (`localStorage`) and is sent per request; the server stores nothing about users. Logs contain method, path and status only. Uploads are processed in memory and the response contains metadata only.

## 5. API

| Method & path | Purpose |
|---|---|
| `GET /api/meta` | Field specs, states, categories, notices |
| `GET /api/schemes`, `GET /api/schemes/{id}` | Cards with freshness flags; documents with clean passages |
| `POST /api/search` | Discovery (filters, optional profile, `language`) |
| `POST /api/agent/run` | Full workflow: search → retrieve → extract → evaluate → checklist, with a trace |
| `POST /api/agent/tool` | One allow-listed tool call (unknown tools → 403, bad args → 422) |
| `POST /api/schemes/{id}/eligibility` · `/checklist` · `/changes` · `/assessment` | Per-scheme results (`assessment` returns everything the detail page needs) |
| `POST /api/ask` | Cited Q&A over passages; abstains without evidence |
| `POST /api/sources/{doc_id}/check` | Source reachability check (honest about failures; no data written) |
| `POST /api/documents/inspect` | Validate an upload (PDF/TXT/MD/HTML); returns metadata only |
| `GET /api/health` | Liveness |

Errors use `{"error": code, "message": ...}`; validation errors list field names and messages but never echo the submitted values.

## 6. Data model

`backend/data/schemes.json` (generated by `scripts/build_demo_data.py`; read-only in memory at run time):

```
scheme: id, name, authority, category, target_groups[], scheme_type, states[], geography,
        description(+_hi), keywords[], aliases[], portal{name,url,verified,note}, application{summary,doc_id,passage_id},
        documents[], rules[], required_documents[]
document: id, title, authority, version, publication_date, effective_date, status
          (current | superseded | unclear | validity_not_established | unavailable),
          last_checked, url, passages[{id,section,text}], facts{deadline,benefit}, status_evidence?
rule: id, doc_id, passage_id, criterion, label(+_hi), attribute, op, value, evidence, mandatory, exception?, ambiguous?
required_document: id, doc_id, passage_id, key, classification (mandatory|optional|conditional), evidence,
                   condition?, how_to_obtain{text, doc_id, passage_id}?
```

**Persistence:** demo storage is the JSON file loaded into memory. PostgreSQL and a vector database (named as potential integrations in the spec) are **not** used in this MVP; BM25 is sufficient at this scale and keeps setup to one command.

Fields added for real data (all optional, so the synthetic fixture is unchanged): scheme `coverage` (`"partial"` blocks "likely eligible"); document `manual_verification`, `reading_note`; passage `verbatim` (false = summary, can never verify an item and is excluded from citable search) and `excerpt`; rule `manual_check` (sourced but not testable here).

## 7. Data sources and adding schemes

### Schemes in the dataset (all read 2026-10-30)

| Scheme | Authority | Source read | Type | Notes |
|---|---|---|---|---|
| PM-USP CSSS (`CSSS-PMUSP`) | Ministry of Education | https://scholarships.gov.in/public/schemeGuidelines/CSSS_GUIDLINES_06022024.pdf | Guidelines | Income ≤ ₹4.5 lakh, no other scholarship, Class XII above 80th percentile (not checkable here). Document list and course rule are summary-only, so unverified. A newer-named file could not be read; **which file is current is not established**. |
| PMS-SC (`PMS-SC`) | Ministry of Social Justice & Empowerment | PIB 12 Aug 2026 (PRID 2298357) and PIB 25 Sep 2023 (PRID 1960387) | Press releases | Income ≤ ₹2.5 lakh, SC, studying in India. Guidelines not read. No document list. |
| PMS-ST (`PMS-ST`) | Ministry of Tribal Affairs | PIB 15 Mar 2023 (PRID 1907241) | Press release | ST, income ≤ ₹2.50 lakh; "class XI and above" left **ambiguous** on purpose. |
| AICTE Pragati (`AICTE-PRAGATI`) | AICTE / Ministry of Education | PIB 8 Dec 2021 (PRID 1779333) | Press release | Girl student, family income < ₹8 lakh, max two girls per family. Nearly five years old: flagged. AICTE's own page could not be read. |
| PM YASASVI post-matric (`PM-YASASVI-PMS`) | Ministry of Social Justice & Empowerment | https://socialjustice.gov.in/public/ckeditor/upload/65661651839791.pdf | Guidelines (Part B) | OBC/EBC/DNT, income ≤ ₹2.50 lakh. The text states a scheme period ending 2025-26, so validity is marked **unclear**. About 100,000 of 119,414 characters were read; the document list was cut off. |

Titles of the PIB releases come from search-result titles. Application URL: none verified for any scheme; each scheme links only to the general National Scholarship Portal, with a note saying so.

### Not read (access refused or not attempted)

Minorities post-matric scholarship (also left out because eligibility depends on religion, which CivicLens does not collect), PMSSS J&K, Top Class Education for SC students, Top Class College (OBC), and the AICTE FAQ. See `meta.sources_not_readable`.

### Adding or refreshing a scheme

1. Open the official document yourself. Copy the exact sentence for each criterion.
2. Edit `scripts/build_real_data.py`: add a `doc(...)` with passages (`verbatim=True` only for text copied exactly), then `rule(...)` / `req(...)` entries whose `evidence` is a substring of that passage. Use `manual_check=True` for conditions CivicLens has no field for, `ambiguous=True` for unclear wording.
3. Leave `effective_date` empty unless the document states it. Set `status="superseded"` and `status_evidence` on an older version only when the newer document says so.
4. Run `python scripts/build_real_data.py`, then `python -m pytest`. The loader refuses to verify any rule whose quote is not found in a verbatim passage.

`python -m app.ingest` can turn a PDF/HTML into draft passages to start from.

## 8. Known limitations and assumptions

* **Not yet verified against the originals.** All wording came through a fetch tool that may have trimmed or normalised text. Treat every figure as "to be confirmed at the official source".
* **Press releases are not guidelines.** PMS-SC, PMS-ST and Pragati rest on PIB statements (2021–2026). They state headline eligibility only; no documents, deadlines or application steps.
* **No scheme ever reaches "likely eligible".** All five are partial coverage. The best result is "undetermined" with every checkable criterion satisfied. The engine still supports "likely eligible" and the test fixtures exercise it.
* **Some conditions cannot be tested** (Class XII percentile, girls per family, year of admission, studying in India). They are shown as sourced but "cannot be checked by this tool".
* **Category list**: SC, ST, OBC, EBC/DNT, EWS, General. CivicLens does not collect religion, so minority schemes are not included.
* **Policy comparison needs two official versions.** None are stored for any scheme (the PMS-SC pair are two press releases, not versions), so no change is reported. A possible newer CSSS file was not readable.
* **No application URLs verified**; only the general National Scholarship Portal is linked, with a note.
* **Scholarship amounts and deadlines** are mostly not recorded (only the CSSS and Pragati benefit figures appear in the data; no deadlines).
* **No scheduler, no OCR, no accounts, no database.** Source checks are on demand; live fetch is off by default and limited to `*.gov.in` / `*.nic.in`.
* **Hindi covers the interface and engine messages, not the data notes.** Scheme validity notes, open questions and the source quotations stay in English.
* **Search is keyword-based (BM25)** with a small Hindi glossary; **Hindi** strings are hand-written and should be reviewed by a native speaker.
* A hosted deployment needs HTTPS, a shared rate-limit store and, if accounts are added, authentication.

## 9. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: app` | Run commands from the `backend/` directory. |
| Blank page / 404 at `/` | The `frontend/` folder must sit next to `backend/` (it is served by the same server). |
| Banner shows but no results | Open `/api/health`; check the terminal for errors; try `CIVICLENS_DATA_PATH` unset. |
| "Too many requests" (429) | Raise `CIVICLENS_RATE_LIMIT_PER_MINUTE` or wait a minute. |
| Ask says "No AI answer was generated" | Expected without `ANTHROPIC_API_KEY`; passages are still shown. With a key, check the `llm_status` field in the response. |
| Hindi text looks like boxes | Install a Devanagari font (e.g. Noto Sans Devanagari). |
| Profile did not persist | Private/blocked browser storage; the app still works but forgets your details on reload. |

## 10. Project layout

```
civiclens/
├── backend/
│   ├── app/            main.py (API) · eligibility.py · checklist.py · changes.py · discovery.py · retrieval.py
│   │                   agent.py · llm.py · security.py · sources.py · store.py · ingest.py · models.py · fields.py · i18n.py
│   ├── data/schemes.json      (5 real schemes, generated)
│   ├── tests/          124 tests (+ fixtures/demo_schemes.json)
│   └── requirements.txt
├── frontend/           index.html · styles.css · app.js  (no build step)
├── ui-tests/           optional jsdom smoke test
├── scripts/build_real_data.py   (real data)  ·  build_demo_data.py (test fixture)
└── .env.example
```


## 11. Trust rules (what the engine will and will not say)

* Search relevance and eligibility are separate: the card shows **Why this matched your search** (your words, your state) and, separately, **Eligibility assessment**.
* Missing answers are **Unknown**, never "Not satisfied". A rule is **Not satisfied** only when it matches the stored source text and your answer clearly fails it.
* "Likely eligible" needs every mandatory criterion satisfied **and** complete source coverage **and** validity that is not unclear/expired/declared-unknown **and** no conflict. Otherwise the result is "undetermined" and the reasons are listed ("Why this is not likely eligible").
* A missing effective date alone produces a warning; it blocks only when a scheme's validity is declared or derived as unclear, expired or unknown.
* Prompts: `backend/app/prompts/extraction_agent.md` (how to extract data) and `planner_agent.md` (relevance vs eligibility); the planner rules are added to the optional LLM prompts. Check a dataset with `python -m app.report [path]`.

## 12. Three-minute demo flow

1. (0:00) Open the app. Point at the banner: real data, read through a fetch tool, not yet checked word for word.
2. (0:20) **My details**: category SC, income 200000, female, undergraduate. Save.
3. (0:45) Search "scholarship for SC students". Show **Why this matched** vs **Eligibility assessment** on each card; note PMS-ST shows "Requirement not met" with the reason.
4. (1:15) Open **PMS-SC → Eligibility**: income and category satisfied, "studying in India" unknown. Read "Why this is not likely eligible".
5. (1:45) **Evidence** tab: exact quoted passage, PIB link, "How this source was read".
6. (2:10) **CSSS → Eligibility**: percentile cannot be checked here; the course rule is unverified. **Checklist** shows "not verified" items; **Policy changes** says nothing to compare.
7. (2:40) Switch to हिन्दी. Close: preliminary assessment only; every figure needs checking at the official source.
