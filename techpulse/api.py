"""
api.py
------

FastAPI service exposing stored, LLM-enriched Hacker News stories.
Run locally with:
    uvicorn techpulse.api:app --reload

endpoints:
    GET /health                -> liveness check
    GET /stories               -> list stories, filterable by category/min_score
    GET /stories/{story_id}    -> fetch a single story
    POST /pipeline/run         -> trigger a fetch+summarize+store cycle
"""

from __future__ import annotations

import os
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from techpulse.pipeline import run_pipeline
from techpulse.storage import StoryRepository

DB_PATH = os.environ.get("TECHPULSE_DB_PATH", "techpulse.db")

app = FastAPI(
    title="TechPulse API",
    description="LLM-enriched Hacker News feed.",
    version="1.0.0",
)

def get_repository() -> StoryRepository:
    return StoryRepository(db_path=DB_PATH)


class StoryResponse(BaseModel):
    id: int
    title: str
    url: Optional[str]
    score: int
    by: str
    summary: Optional[str]
    category: Optional[str]
    fetched_at: str


class PipelineRunResponse(BaseModel):
    processed: int
    message: str


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}

@app.get("/stories", response_model=list[StoryResponse])
def list_stories(
    category: Optional[str] = Query(default=None, description="Filter by category, e.g. 'AI/ML'"),
    min_score: int = Query(default=0, ge=0, description="Minimum HN score"),
    limit: int = Query(default=50, ge=1, le=200),
    repo: StoryRepository = Depends(get_repository),
):
    rows = repo.list_stories(category=category, min_score=min_score, limit=limit)
    return [dict(row) for row in rows]

@app.get("/stories/{story_id}", response_model=StoryResponse)
def get_story(story_id: int, repo: StoryRepository = Depends(get_repository)):
    row = repo.get_by_id(story_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")
    return dict(row)

@app.post("/pipeline/run", response_model=PipelineRunResponse)
def trigger_pipeline_run(limit: int = Query(default=20, ge=1, le=100)):
    processed = run_pipeline(limit=limit, db_path=DB_PATH)
    return PipelineRunResponse(
        processed=processed,
        message=f"Pipeline run complete. {processed} stories processed.",
    )
