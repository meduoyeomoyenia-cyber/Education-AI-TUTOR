"""ALOC question API adapter (first provider).

Config (environment variables — never hardcode the key):
  ALOC_API_KEY   API key, sent as the X-API-Key request header (required for live fetch)
  ALOC_BASE_URL  API base URL, e.g. https://dev.aloc.com.ng (required for live fetch)
  ALOC_QUESTIONS_PATH  questions endpoint path (default: /api/v1/questions)
  ALOC_KEY_HEADER  header name carrying the key (default: X-API-Key)
  ALOC_LICENSE   license/provenance string stamped on imports (default: "")

Endpoint paths + response mapping: filled from the owner's API details.
Until confirmed, fetch() raises NotConfigured with setup instructions.
"""
import os
import httpx
from .base import QuestionProvider, register

# Map provider subject/exam labels to ours. Keys are LOWER-CASED provider
# labels; adjust once the owner confirms exact ALOC values.
SUBJECT_MAP = {
    "mathematics": "Mathematics",
    "english": "English Language",
    "physics": "Physics",
    "chemistry": "Chemistry",
    "biology": "Biology",
}
EXAM_MAP = {
    "waec": "WAEC",
    "jamb": "JAMB",
    "utme": "JAMB",
    "neco": "NECO",
}


class NotConfigured(RuntimeError):
    pass


class AlocProvider(QuestionProvider):
    name = "aloc"

    def __init__(self, api_key: str | None = None, base_url: str | None = None,
                 key_header: str | None = None, questions_path: str | None = None,
                 timeout: int = 20, client: httpx.Client | None = None):
        self.api_key = api_key if api_key is not None else os.getenv("ALOC_API_KEY", "")
        self.base_url = (base_url if base_url is not None else os.getenv("ALOC_BASE_URL", "")).rstrip("/")
        self.questions_path = questions_path or os.getenv("ALOC_QUESTIONS_PATH", "/api/v1/questions")
        self.key_header = key_header or os.getenv("ALOC_KEY_HEADER", "X-API-Key")
        self.timeout = timeout
        self._client = client

    def _check_config(self):
        missing = []
        if not self.api_key:
            missing.append("ALOC_API_KEY")
        if not self.base_url:
            missing.append("ALOC_BASE_URL")
        if missing:
            raise NotConfigured(
                "ALOC provider not configured (missing: %s). Set env vars and retry." % ", ".join(missing))

    def _get(self, path: str, params: dict) -> dict:
        self._check_config()
        client = self._client or httpx.Client(timeout=self.timeout)
        try:
            r = client.get(f"{self.base_url}{path}", params=params,
                           headers={self.key_header: self.api_key})
            r.raise_for_status()
            return r.json()
        finally:
            if self._client is None:
                client.close()

    def fetch(self, subject: str, exam: str, topic: str | None = None, limit: int = 20) -> list:
        """Fetch raw question records. Path/params follow the owner's API details."""
        params = {"subject": subject.lower(), "examType": exam.lower(), "limit": limit}
        if topic:
            params["topic"] = topic
        data = self._get(self.questions_path, params)
        if isinstance(data, dict):
            for key in ("data", "results", "questions"):
                if isinstance(data.get(key), list):
                    return data[key][:limit]
            raise ValueError("ALOC: unexpected response shape (no question list found).")
        return list(data)[:limit]

    def normalize(self, raw: dict, subject: str, exam: str) -> dict:
        """Map raw ALOC record -> ingestion schema. Field names mirror the
        observed live response (text/correctAnswer/options/id/provenance).
        Topic candidates: explicit topic first, then section/category ONLY as
        unconfirmed candidates — validate() exact-matches them against existing
        Topics and NEVER auto-creates. License is never invented: ALOC_LICENSE
        env or blank (blank -> NEEDS_REVIEW by Step 4B rules)."""
        options = raw.get("options") or raw.get("choices") or []
        if isinstance(options, dict):
            options = [options.get(k) for k in ("A", "B", "C", "D") if options.get(k) is not None]
        given = str(raw.get("correctAnswer") or raw.get("answer") or "").strip()
        answer = given
        if len(given) == 1 and given.upper() in "ABCD":
            idx = "ABCD".index(given.upper())
            if idx < len(options or []):
                answer = str(options[idx]).strip()  # store resolved option TEXT
        # else: out-of-range letter, missing option, or already full text -> leave
        # unresolved so generic validation flags NEEDS_REVIEW (never guessed here)
        return {
            "question_text": (raw.get("text") or raw.get("question") or raw.get("question_text") or "").strip(),
            "options": options,
            "answer": answer,
            "explanation": (raw.get("explanation") or raw.get("solution") or ""),
            "subject": SUBJECT_MAP.get(subject.lower(), subject),
            "topic": (raw.get("topic") or raw.get("section") or raw.get("category") or ""),
            "exam_style": EXAM_MAP.get(exam.lower(), exam.upper()),
            "difficulty": raw.get("difficulty") or "Basic",
            "source": "aloc",
            "source_reference": str(raw.get("id") or raw.get("question_id") or ""),
            "license": os.getenv("ALOC_LICENSE", ""),
        }


register(AlocProvider())
