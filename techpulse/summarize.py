"""
summarize.py
------------

Uses an LLM backedn (via OpenRouterClient - see llm.py) to turn raw Hacker News
story into a short summary and a category tag.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

from techpulse.fetcher import Story
from techpulse.llm import OpenRouterClient

logger = logging.getLogger(__name__)

ALLOWED_CATEGORIES = [
    "AI/ML",
    "Security",
    "Programming",
    "Startups",
    "Hardware",
    "Science",
    "Other"
]

SYSTEM_PROMPT = f"""
    You are a technical news editor. Given a Hacker News Story's title and URL, respond with \
    ONLY a JSON object (no markdown, no preamble) with exactly two keys: \
    - "summary": a single sentece (max 30 words) guessing what the story is about
    - "category": exactly one of {ALLOWED_CATEGORIES}

    If you're unsure of the content from the title alone, make your best reasonable guess
    rather than refusing.
"""

@dataclass
class Enrichment:
    summary: str
    category: str


class StorySummarizer:
    def __init__(self, client: OpenRouterClient | None = None):
        self._client = client or OpenRouterClient()

    def summarize(self, story: Story) -> Enrichment:
        user_prompt = f"Title: {story.title}\nURL: {story.url or "N/A"}"
        raw_text = self._client.complete(system=SYSTEM_PROMPT, user=user_prompt)
        return self._parse_response(raw_text)

    @staticmethod
    def _parse_response(raw_text: str) -> Enrichment:
        cleaned = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

        try:
            data = json.loads(cleaned)
            summary = str(data.get("summary", "")).strip() or "(no summary available)"
            category = str(data.get("category", "")).strip()

            if category not in ALLOWED_CATEGORIES:
                category = "Other"

            return Enrichment(summary=summary, category=category)
        except (json.JSONDecodeError, AttributeError) as exc:
            logger.warning("Failed to parse LLM reponse as JSON: %s | raw = %r", exc, raw_text)
            return Enrichment(summary="(no summary available)", category="Other")