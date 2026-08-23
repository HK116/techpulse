"""
Tests for techpulse.storage

Uses a temporary on-disk SQLite file per test (via pytest's tmp_path fixture)
so tests never touch real db and stay isolated
"""

import pytest

from techpulse.fetcher import Story
from techpulse.storage import EnrichedStory, StoryRepository


def make_story(id=1, title="Test story", score=10) -> Story:
    return Story(id=id, title=title, url="https://example.com", score=score, by="testuser", time=1700000000)
    
@pytest.fixture    
def repo(tmp_path):
    db_file = tmp_path / "test.db"
    return StoryRepository(db_path=str(db_file))
    
def test_upser_and_get_by_id(repo):
    enriched = EnrichedStory(story=make_story(id=1), summary="A summary", category="AI")
    repo.upsert(enriched)

    row = repo.get_by_id(1)

    assert row is not None
    assert row["title"] == "Test story"
    assert row["summary"] == "A summary"
    assert row["category"] == "AI"

def test_upsert_updates_existing_row_on_conflict(repo):
    repo.upsert(EnrichedStory(story=make_story(id=1, score=10), summary="old"))
    repo.upsert(EnrichedStory(story=make_story(id=1, score=99), summary="new"))

    row = repo.get_by_id(1)

    assert row["score"] == 99
    assert row["summary"] == "new"
    assert repo.count() == 1 # no duplicate row

def test_list_stories_filters_by_min_score(repo):
    repo.upsert(EnrichedStory(story=make_story(id=1, score=5)))
    repo.upsert(EnrichedStory(story=make_story(id=2, score=50)))

    results = repo.list_stories(min_score=10)

    assert len(results) == 1
    assert results[0]["id"] == 2

def test_list_stories_filters_by_category(repo):
    repo.upsert(EnrichedStory(story=make_story(id=1, score=10), category="AI"))
    repo.upsert(EnrichedStory(story=make_story(id=2, score=20), category="Security"))

    results = repo.list_stories(category="Security")

    assert len(results) == 1
    assert results[0]["id"] == 2

def test_list_stories_orders_by_score_descending(repo):
    repo.upsert(EnrichedStory(story=make_story(id=1, score=5)))
    repo.upsert(EnrichedStory(story=make_story(id=2, score=50)))
    repo.upsert(EnrichedStory(story=make_story(id=3, score=25)))

    results = repo.list_stories(min_score=0)

    scores = [r["score"] for r in results]
    assert scores == sorted(scores, reverse=True)

def test_bulk_upsert(repo):
    stories = [EnrichedStory(story=make_story(id=i, score=i * 10)) for i in range(1, 6)]
    repo.bulk_upsert(stories)

    assert repo.count() == 5

