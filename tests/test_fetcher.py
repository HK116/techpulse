"""
Test for techpulse.fetcher

Everything is mocker here. runnable offline / CLI
"""

from unittest.mock import MagicMock

import pytest

from techpulse.fetcher import HackerNewsClient, Story

SAMPLE_STORY_PAYLOAD = {
    "id" : 123,
    "type" : "story",
    "title" : "Show HN. I built a thing",
    "url" : "https://example.com/thing",
    "score" : 150,
    "by" : "someuser",
    "time" : 1700000000,
    "descendants" : 42,
}

def _mock_response(json_data, status_code=200):
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = MagicMock()

    return mock_resp


def test_story_from_api_payload_maps_fileds_correctly():
    story = Story.from_api_payload(SAMPLE_STORY_PAYLOAD)

    assert story.id == 123
    assert story.title == "Show HN. I built a thing"
    assert story.url == "https://example.com/thing"
    assert story.score == 150
    assert story.by == "someuser"
    assert story.descendants == 42


def test_story_from_api_payload_handles_missing_optional_fields():
    minimal_payload = {"id": 1}
    story = Story.from_api_payload(minimal_payload)

    assert story.title == "(no title)"
    assert story.url is None
    assert story.score == 0
    assert story.descendants == 0


def test_get_top_story_ids_returns_limited_list():
    session = MagicMock()
    session.get.return_value = _mock_response(list(range(1, 501)))

    client = HackerNewsClient(session=session)
    ids = client.get_top_story_ids(limit=10)

    assert ids == list(range(1, 11))
    session.get.assert_called_once()


def test_get_story_returns_none_for_deleted_item():
    session = MagicMock()
    session.get.return_value = _mock_response({"id": 5, "type": "comment"})

    client = HackerNewsClient(session=session)
    result = client.get_story(5)

    assert result == None


def test_get_story_returns_none_for_non_story_type():
    session = MagicMock()
    session.get.return_value = _mock_response({"id": 5, "deleted": True})
    
    client = HackerNewsClient(session=session)
    result = client.get_story(5)
    
    assert result == None


def test_get_story_parses_valid_story():
    session = MagicMock()
    session.get.return_value = _mock_response(SAMPLE_STORY_PAYLOAD)

    client = HackerNewsClient(session=session)
    result = client.get_story(123)

    assert isinstance(result, Story)
    assert result.title == "Show HN. I built a thing"


def teset_get_top_stories_skips_none_results():
    session = MagicMock()
    session.get.side_effect = [
        _mock_response([1, 2]),
        _mock_response(SAMPLE_STORY_PAYLOAD),
        _mock_response({"id": 2, "deleted": True}),
    ]

    client = HackerNewsClient(session=session)
    stories = client.get_top_stories(limit=2)

    assert len(stories) == 1
    assert stories[0].id == 123