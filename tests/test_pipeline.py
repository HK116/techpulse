"""
Tests for techpulse.pipeline.

The whole pipeline is tested with fake fetcher/summarizer/repo objects,
so it runs instantly with no network, no API key, and no real database.
"""

from techpulse.fetcher import Story
from techpulse.pipeline import run_pipeline
from techpulse.summarize import Enrichment


class FakeFetcher:
    def __init__(self, stories):
        self._stories = stories

    def get_top_stories(self, limit):
        return self._stories[:limit]


class FakeSummarizer:
    def __init__(self, fail_on_ids=None):
        self.fail_on_ids = fail_on_ids or set()

    def summarize(self, story):
        if story.id in self.fail_on_ids:
            raise RuntimeError("simulated LLM failure")
        return Enrichment(summary=f"Summary of {story.title}", category="Programming")


class FakeRepo:
    def __init__(self):
        self.saved = []

    def upsert(self, enriched_story):
        self.saved.append(enriched_story)


def make_story(id) -> Story:
    return Story(id=id, title=f"Story {id}", url=None, score=id * 10, by="tester", time=1700000000)


def test_pipeline_processes_all_stories_successfully():
    stories = [make_story(1), make_story(2), make_story(3)]
    fetcher = FakeFetcher(stories)
    summarizer = FakeSummarizer()
    repo = FakeRepo()

    processed = run_pipeline(limit=3, fetcher=fetcher, summarizer=summarizer, repo=repo)

    assert processed == 3
    assert len(repo.saved) == 3
    assert repo.saved[0].summary == "Summary of Story 1"
    assert repo.saved[0].category == "Programming"


def test_pipeline_skips_failed_stories_without_crashing():
    stories = [make_story(1), make_story(2), make_story(3)]
    fetcher = FakeFetcher(stories)
    summarizer = FakeSummarizer(fail_on_ids={2})
    repo = FakeRepo()

    processed = run_pipeline(limit=3, fetcher=fetcher, summarizer=summarizer, repo=repo)

    assert processed == 2
    saved_ids = [s.story.id for s in repo.saved]
    assert saved_ids == [1, 3]


def test_pipeline_respects_limit():
    stories = [make_story(i) for i in range(1, 11)]
    fetcher = FakeFetcher(stories)
    summarizer = FakeSummarizer()
    repo = FakeRepo()

    processed = run_pipeline(limit=4, fetcher=fetcher, summarizer=summarizer, repo=repo)

    assert processed == 4
    assert len(repo.saved) == 4


def test_pipeline_returns_zero_when_no_stories_found():
    fetcher = FakeFetcher([])
    summarizer = FakeSummarizer()
    repo = FakeRepo()

    processed = run_pipeline(limit=5, fetcher=fetcher, summarizer=summarizer, repo=repo)

    assert processed == 0
    assert repo.saved == []