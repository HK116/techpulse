"""
fetcher.py
----------

Handles communication with the public Hacker News (Firebase) API.

Docs: https://github.com/HackerNews/API
NO API KEY REQUIRED
'"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional

import requests

logger = logging.getLogger(__name__)

HN_BASE_URL = "https://hacker-news.firebaseio.com/v0"
TOP_STORIES_ENDPOINT = f"{HN_BASE_URL}/topstories.json"
ITEM_ENDPOINT_TEMPLATE = f"{HN_BASE_URL}/item/{{item_id}}.json"

DEFAULT_TIMEOUT_SECONDS = 10


@dataclass
class Story:
    """A single Hacker News story, normalized to the fields we care about."""

    id: int
    title: str
    url: Optional[str]
    score: int
    by: str
    time: int
    descendants: int = 0  # comment count

    @classmethod
    def from_api_payload(cls, payload: dict) -> "Story":
        return cls(
            id=payload["id"],
            title=payload.get("title", "(no title)"),
            url = payload.get("url"),
            score = payload.get("score", 0),
            by = payload.get("by", "unknown"),
            time = payload.get("time", 0),
            descendants = payload.get("descendants", 0),
        )


class HackerNewsClient:
    """Thin wrapper around the Hacker News API."""

    def __init__(self, session: Optional[requests.Session] = None, timeout: int = DEFAULT_TIMEOUT_SECONDS):
        self._session = session or requests.Session()
        self._timeout = timeout

    def get_top_story_ids(self, limit: int = 30) -> List[int]:
        """Return up to `limit` top story IDs, ranked by HN's own ordering."""
        response = self._session.get(TOP_STORIES_ENDPOINT, timeout=self._timeout)
        response.raise_for_status()
        story_ids = response.json()
        return story_ids[:limit]

    def get_story(self, story_id: int) -> Optional[Story]:
        """Fetch a single story by ID. Return None if the item is missing or deleted."""
        url = ITEM_ENDPOINT_TEMPLATE.format(item_id = story_id)
        response = self._session.get(url, timeout=self._timeout)
        response.raise_for_status()
        payload = response.json()

        if not payload or payload.get("deleted") or payload.get("dead"):
            logger.debug("Skipping missing/deleted/dead story id=%s", story_id)
            return None

        if payload.get("type") != "story":
            logger.debug("Skipping non-story item id=%s", story_id)
            return None

        return Story.from_api_payload(payload)

    def get_top_stories(self, limit: int = 30) -> List[Story]:
        """Fetch and return upto `limit` fully-populated top stories."""
        story_ids = self.get_top_story_ids(limit=limit)
        stories: List[Story] = []
        for story_id in story_ids:
            story = self.get_story(story_id)
            if story is not None:
                stories.append(story)

        return stories