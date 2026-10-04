"""Provider architecture: external question APIs plug in here.

A provider fetches raw external questions and normalizes them into the
ingestion schema (question_text, options, answer, explanation, subject,
topic, exam_style, difficulty, source, source_reference, license).
Normalized rows ALWAYS go through staging + teacher review; providers
can never write directly to the production Question table.
"""
from abc import ABC, abstractmethod


class QuestionProvider(ABC):
    name: str = "base"

    @abstractmethod
    def fetch(self, subject: str, exam: str, topic: str | None = None, limit: int = 20) -> list:
        """Return RAW external records (provider-native shape). May raise."""

    @abstractmethod
    def normalize(self, raw: dict, subject: str, exam: str) -> dict:
        """Map one raw record to the ingestion schema. Must set source."""

    def fetch_normalized(self, subject: str, exam: str, topic: str | None = None, limit: int = 20) -> list:
        return [self.normalize(r, subject, exam) for r in self.fetch(subject, exam, topic, limit)]


_PROVIDERS: dict = {}


def register(provider: QuestionProvider):
    _PROVIDERS[provider.name] = provider


def get_provider(name: str) -> QuestionProvider:
    try:
        return _PROVIDERS[name]
    except KeyError:
        raise ValueError(f"Unknown provider: {name}. Available: {sorted(_PROVIDERS)}")


def provider_names() -> list:
    return sorted(_PROVIDERS)
