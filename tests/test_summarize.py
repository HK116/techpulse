"""
Tests for techpulse.summarizer.

No real API key or network call is ever used here — we inject a fake
backend implementing the same `complete()` interface as the real ones.
"""

from techpulse.fetcher import Story
from techpulse.summarize import Enrichment, StorySummarizer


def make_story() -> Story:
    return Story(
        id=1,
        title="New transformer architecture claims 2x training speedup",
        url="https://example.com/paper",
        score=200,
        by="researcher",
        time=1700000000,
    )


class FakeBackend:
    def __init__(self, response_text: str):
        self._response_text = response_text
        self.last_system = None
        self.last_user = None

    def complete(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        return self._response_text


def test_summarize_parses_valid_json_response():
    backend = FakeBackend('{"summary": "A faster transformer training method.", "category": "AI/ML"}')
    summarizer = StorySummarizer(backend=backend)

    result = summarizer.summarize(make_story())

    assert isinstance(result, Enrichment)
    assert result.summary == "A faster transformer training method."
    assert result.category == "AI/ML"


def test_summarize_strips_markdown_code_fences():
    backend = FakeBackend('```json\n{"summary": "Test summary", "category": "Programming"}\n```')
    summarizer = StorySummarizer(backend=backend)

    result = summarizer.summarize(make_story())

    assert result.summary == "Test summary"
    assert result.category == "Programming"


def test_summarize_falls_back_to_other_for_invalid_category():
    backend = FakeBackend('{"summary": "Some summary", "category": "NotARealCategory"}')
    summarizer = StorySummarizer(backend=backend)

    result = summarizer.summarize(make_story())

    assert result.category == "Other"


def test_summarize_handles_malformed_json_gracefully():
    backend = FakeBackend("this is not json at all")
    summarizer = StorySummarizer(backend=backend)

    result = summarizer.summarize(make_story())

    assert result.summary == "(no summary available)"
    assert result.category == "Other"


def test_summarize_sends_story_title_and_url_in_prompt():
    backend = FakeBackend('{"summary": "x", "category": "Other"}')
    summarizer = StorySummarizer(backend=backend)

    summarizer.summarize(make_story())

    assert backend.last_user is not None
    assert "New transformer architecture" in backend.last_user
    assert "https://example.com/paper" in backend.last_user