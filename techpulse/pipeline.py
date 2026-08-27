"""
pipline.py
----------

Orchestrates the end-to-end flow: fetch -> summarize with an LLM -> persist in storage.
The CLI and API's /pipeline/run endpoints call this module.
"""

from __future__ import annotations

import logging

from techpulse.fetcher import HackerNewsClient
from techpulse.storage import EnrichedStory, StoryRepository
from techpulse.summarize import StorySummarizer

logger = logging.getLogger(__name__)


def run_pipeline(
    limit: int = 10,
    db_path: str = "techpulse.db",
    fetcher: HackerNewsClient | None = None,
    summarizer: StorySummarizer | None = None,
    repo: StoryRepository | None = None,
) -> int:
    """
    Run on full fetch -> summarize -> store cycle.
    Returns the number of stories successfully processed.
    """

    fetcher = fetcher or HackerNewsClient()
    summarizer = summarizer or StorySummarizer()
    repo = repo or StoryRepository(db_path=db_path)

    logger.info("Fetching top %d stories from Hacker News", limit)
    stories = fetcher.get_top_stories(limit=limit)
    logger.info("Fetched %d stories.", limit)

    processed = 0
    for story in stories:
        try:
            enrichment = summarizer.summarize(story)
            repo.upsert(
                EnrichedStory(
                    story=story,
                    summary=enrichment.summary,
                    category=enrichment.category,
                )
            )
            processed += 1
        except Exception:
            logger.exception("Failed to process story id=%s, skipping.", story.id)

    logger.info("Pipeline complete. Processed %d/%d stories", processed, len(stories))
    return processed