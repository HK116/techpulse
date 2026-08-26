"""
Tests for techpulse.api.

Uses FastAPI's dependency override system to inject a repository backed
by a temporary SQLite file, so no real database or network call is needed.
"""

import pytest
from fastapi.testclient import TestClient

from techpulse.api import app, get_repository
from techpulse.fetcher import Story
from techpulse.storage import EnrichedStory, StoryRepository


@pytest.fixture
def client(tmp_path):
    db_file = tmp_path / "api_test.db"
    repo = StoryRepository(db_path=str(db_file))

    repo.upsert(
        EnrichedStory(
            story=Story(id=1, title="AI breakthrough", url="https://z.com", score=100, by="a", time=1),
            summary="An AI breakthrough happened.",
            category="AI/ML",
        )
    )
    repo.upsert(
        EnrichedStory(
            story=Story(id=2, title="New CVE disclosed", url="https://y.com", score=50, by="b", time=2),
            summary="A security vulnerability was disclosed.",
            category="Security",
        )
    )

    app.dependency_overrides[get_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_stories_returns_all_by_default(client):
    response = client.get("/stories")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_stories_filters_by_category(client):
    response = client.get("/stories", params={"category": "Security"})
    data = response.json()
    assert len(data) == 1
    assert data[0]["category"] == "Security"


def test_list_stories_filters_by_min_score(client):
    response = client.get("/stories", params={"min_score": 75})
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == 1


def test_get_story_by_id_returns_story(client):
    response = client.get("/stories/1")
    assert response.status_code == 200
    assert response.json()["title"] == "AI breakthrough"


def test_get_story_by_id_returns_404_for_missing_story(client):
    response = client.get("/stories/999")
    assert response.status_code == 404