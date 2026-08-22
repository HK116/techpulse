"""
storage.py
----------

SQLite persistence layer for stories and their LLM-generated summaries.

Kept dependency-light (stdblib sqlite3) so the project runs anywhere with 
zero extra infrastructure, while still modeling a real schema to extend to Postgres in prod
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterator, List, Optional

from techpulse.fetcher import Story

SCHEMA = """
CREATE TABLE IF NOT EXISTS stories (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    url TEXT, 
    score INTEGER NOT NULL DEFAULT 0,
    by TEXT NOT NULL,
    time INTEGER NOT NULL,
    descendants INTEGER NOT NULL DEFAULT 0,
    summary TEXT,
    category TEXT,
    fetched_at TEXT NOT NULL
);
"""

@dataclass
class EnrichedStory:
    """A Story plus the fileds the LLM adds on top."""

    story: Story
    summary: Optional[str] = None
    category: Optional[str] = None
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())



class StoryRepository:
    """Handles all reads/writes to the stories table."""

    def __init__(self, db_path: str = "techpulse.db"):
        self.db_path = db_path
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self):
        with self._connect() as conn:
            conn.execute(SCHEMA)

    def upsert(self, enriched: EnrichedStory) -> None:
        """Insert a story, or Update it if it already exists (by id). upsert = update or insert"""
        s = enriched.story
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO stories (id, title, url, score, by, time, descendants, summary, category, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title=excluded.title,
                    url=excluded.url,
                    score=excluded.score,
                    descendants=excluded.descendants,
                    summary=excluded.summary,
                    category=excluded.category,
                    fetched_at=excluded.fetched_at
                """,
                (
                    s.id,
                    s.title,
                    s.url,
                    s.score,
                    s.by,
                    s.time,
                    s.descendants,
                    enriched.summary,
                    enriched.category,
                    enriched.fetched_at,
                ),
            )

    def bulk_upsert(self, enriched_stories: List[EnrichedStory]) -> None:
        for item in enriched_stories:
            self.upsert(item)

    def get_by_id(self, story_id: int) -> Optional[sqlite3.Row]:
        with self._connect() as conn:
            cursor = conn.execute("SELECT * FROM stories WHERE id = ?", (story_id,))
            return cursor.fetchone()

    def list_stories(
        self,
        category: Optional[str] = None,
        min_score: int = 0,
        limit: int = 50,
    ) -> List[sqlite3.Row]:
        query = "SELECT * FROM stories WHERE score >= ?"
        params: list = [min_score]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " ORDER BY score DESC LIMIT ?"
        params.append(limit)

        with self._connect() as conn:
            cursor = conn.execute(query, params)
            return cursor.fetchall()

    def count(self) -> int:
        with self._connect() as conn:
            cursor = conn.execute("SELECT COUNT(*) as c FROM stories")
            return cursor.fetchone()["c"]