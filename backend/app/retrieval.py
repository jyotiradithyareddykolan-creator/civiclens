"""Hybrid-lite retrieval: BM25 over scheme text and over document passages (pure Python, no heavy deps).

Hindi queries are mapped to English index terms with a small glossary. Retrieval relevance is NOT eligibility.
"""
import math
import re
from collections import Counter

from .fields import STATES
from .store import Store

TOKEN_RE = re.compile(r"[A-Za-z0-9ऀ-ॿ]+")
DEVANAGARI_RE = re.compile(r"[ऀ-ॿ]")

STOP = {
    "a", "an", "the", "is", "are", "was", "for", "of", "to", "in", "on", "and", "or", "i", "me", "my", "am", "can", "do",
    "does", "what", "which", "who", "how", "get", "find", "show", "tell", "about", "any", "there", "with", "that", "this",
    "scheme", "schemes", "yojana", "government", "govt", "eligibility", "eligible", "apply", "application", "benefit",
    "benefits", "available", "need", "want", "looking", "please", "help", "india", "indian", "be", "it", "if", "under",
    "should", "would", "will", "have", "has", "from", "by", "at", "as", "all", "some", "more", "also", "not", "you", "your",
    "samman", "program", "programme", "support",
    "के", "की", "का", "में", "मुझे", "लिए", "कौन", "सी", "है", "हैं", "मेरे", "मैं", "बताओ", "बताइए", "कृपया", "और", "से",
    "को", "पर", "क्या", "कोई", "योजना", "योजनाएं", "योजनाएँ", "सरकारी", "सरकार", "चाहिए", "मेरी", "मेरा",
}

SYN = {"women": "woman", "womens": "woman", "female": "woman", "ladies": "woman", "elderly": "senior",
       "seniors": "senior", "jobless": "unemployed", "employment": "job", "jobs": "job", "housing": "house"}

HI_GLOSS = {
    "छात्र": ["student"], "छात्रा": ["student"], "छात्रों": ["student"], "छात्राओं": ["student"], "विद्यार्थी": ["student"],
    "छात्रवृत्ति": ["scholarship"], "शिक्षा": ["education", "student"], "कॉलेज": ["college"],
    "किसान": ["farmer"], "किसानों": ["farmer"], "खेती": ["farming", "cultivation"], "कृषि": ["agriculture"],
    "महिला": ["woman"], "महिलाओं": ["woman"], "महिलाएं": ["woman"], "महिलाएँ": ["woman"],
    "उद्यमी": ["entrepreneur"], "व्यवसाय": ["business", "enterprise"], "उद्यम": ["enterprise"],
    "पेंशन": ["pension"], "वरिष्ठ": ["senior"], "बुजुर्ग": ["senior", "elderly"], "वृद्ध": ["senior", "elderly"],
    "नागरिक": ["citizen"], "रोजगार": ["job", "employment"], "नौकरी": ["job"], "बेरोजगार": ["unemployed"],
    "कौशल": ["skill"], "प्रशिक्षण": ["training"], "युवा": ["youth"], "मकान": ["house"], "घर": ["house"],
    "आवास": ["house"], "स्वास्थ्य": ["health"], "आय": ["income"],
    "दिल्ली": ["delhi"], "महाराष्ट्र": ["maharashtra"],
}


def stem(tok: str) -> str:
    if tok in SYN:
        return SYN[tok]
    if len(tok) > 4 and tok.endswith("ies"):
        return tok[:-3] + "y"
    if len(tok) > 3 and tok.endswith("s") and not tok.endswith("ss"):
        return tok[:-1]
    return tok


def detect_language(text: str) -> str:
    return "hi" if DEVANAGARI_RE.search(text or "") else "en"


def tokenize(text: str, expand_hindi: bool = True) -> list[str]:
    out = []
    for raw in TOKEN_RE.findall((text or "").lower()):
        if raw in STOP:
            continue
        if DEVANAGARI_RE.search(raw):
            if expand_hindi:
                out.extend(stem(x) for x in HI_GLOSS.get(raw, []))
            continue
        if raw.isdigit() or len(raw) < 2:
            continue
        out.append(stem(raw))
    return out


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(d) for d in docs]
        self.len = [len(d) for d in docs]
        self.avg = (sum(self.len) / len(self.len)) if self.len else 0.0
        df = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def score(self, query: list[str]) -> list[float]:
        scores = []
        for tf, ln in zip(self.docs, self.len):
            s = 0.0
            for q in set(query):
                f = tf.get(q, 0)
                if not f:
                    continue
                s += self.idf[q] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * ln / (self.avg or 1)))
            scores.append(s)
        return scores

    def matched(self, i: int, query: list[str]) -> list[str]:
        return sorted({q for q in query if self.docs[i].get(q)})


def scheme_text(s: dict) -> str:
    parts = [s["name"], s["name"], s["description"], " ".join(s.get("keywords", [])), " ".join(s.get("target_groups", [])),
             s.get("category", ""), s.get("scheme_type", ""), s.get("geography", "")]
    for d in s.get("documents", []):
        if d.get("status") == "superseded":
            continue
        for p in d["passages"]:
            if not p["flagged"]:  # instruction-like passages never enter the index
                parts.append(p["text"])
    return " ".join(parts)


class SchemeIndex:
    def __init__(self, store: Store):
        self.store = store
        self.ids = list(store.schemes)
        self.scheme_bm25 = BM25([tokenize(scheme_text(store.schemes[i]), expand_hindi=False) for i in self.ids])
        self.passages: list[dict] = []
        for sid in self.ids:
            for d in store.schemes[sid]["documents"]:
                if d.get("status") == "superseded" or d.get("retrieval_status", "ok") != "ok":
                    continue
                for p in d["passages"]:
                    if p["flagged"] or p.get("verbatim", True) is False:  # summaries are never offered as citable quotes
                        continue
                    self.passages.append({"scheme_id": sid, "doc_id": d["id"], "passage_id": p["id"],
                                          "section": p["section"], "text": p["text"]})
        self.passage_bm25 = BM25([tokenize(p["section"] + " " + p["text"], expand_hindi=False) for p in self.passages])

    def search_schemes(self, query_tokens: list[str]) -> dict[str, tuple[float, list[str]]]:
        scores = self.scheme_bm25.score(query_tokens)
        return {sid: (sc, self.scheme_bm25.matched(i, query_tokens)) for i, (sid, sc) in enumerate(zip(self.ids, scores))}

    def retrieve_passages(self, query: str, scheme_id: str | None = None, k: int = 4) -> list[dict]:
        q = tokenize(query)
        if not q:
            return []
        scores = self.passage_bm25.score(q)
        ranked = []
        for i, sc in enumerate(scores):
            p = self.passages[i]
            if sc <= 0 or (scheme_id and p["scheme_id"] != scheme_id):
                continue
            matched = self.passage_bm25.matched(i, q)
            ranked.append({**p, "score": round(sc, 3), "matched_terms": matched})
        ranked.sort(key=lambda x: -x["score"])
        # require enough distinct query terms to match, otherwise abstain
        need = max(1, math.ceil(len(set(q)) / 3))
        return [r for r in ranked if len(r["matched_terms"]) >= need][:k]


_index: SchemeIndex | None = None
_index_for: Store | None = None


def get_index(store: Store) -> SchemeIndex:
    global _index, _index_for
    if _index is None or _index_for is not store:
        _index, _index_for = SchemeIndex(store), store
    return _index


# ---------------------------------------------------------------- unverified named-scheme detection
_CAP_SEQ = re.compile(r"\b(?:[A-Z][A-Za-z]*(?:-[A-Za-z]+)*)(?:\s+[A-Z][A-Za-z]*(?:-[A-Za-z]+)*)+\b|\b[A-Z]{2,}(?:-[A-Z]{2,})+\b")
_BENIGN = {"sc", "st", "obc", "ews", "bpl", "apl"}


def detect_named_scheme(query: str, store: Store) -> dict | None:
    """Heuristic: does the question name a specific scheme that we do not cover?

    Looks for capitalised multi-word names or hyphenated acronyms (e.g. 'PM-KISAN') containing words that are
    not ordinary vocabulary of the covered schemes. Returns {'name', 'verified'} or None.
    """
    vocab = set()
    for s in store.schemes.values():
        vocab.update(w.lower() for w in TOKEN_RE.findall(s["name"] + " " + " ".join(s.get("keywords", []))))
        for a in s.get("aliases", []):
            vocab.update(w.lower() for w in TOKEN_RE.findall(a))
    vocab.update(STOP)
    vocab.update(w.lower() for st in STATES for w in TOKEN_RE.findall(st))
    for m in _CAP_SEQ.finditer(query or ""):
        phrase = m.group(0).strip()
        words = [w.lower() for w in TOKEN_RE.findall(phrase)]
        if all(w in vocab or w in _BENIGN for w in words):
            continue
        low = phrase.lower()
        verified = any(low in s["name"].lower() or any(low == a.lower() for a in s.get("aliases", []))
                       for s in store.schemes.values())
        return {"name": phrase, "verified": verified}
    return None
