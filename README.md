markdown
# TechPulse

A small end-to-end data pipeline that fetches trending Hacker News stories,
uses an LLM (via OpenRouter) to summarize and categorize each one, stores
the results in SQLite, and serves them through a FastAPI service.

Built as a portfolio project to demonstrate practical LLM-integration and
data-engineering fundamentals: external API integration, persistence,
LLM prompting with defensive output parsing, retry/backoff handling for
flaky upstream providers, a real web API with dependency injection, and
a fully mocked test suite.

## Architecture

Hacker News API OpenRouter (any model)
| |
v v
+-----------+ Story +--------------------+ Enrichment +-----------+
| fetcher.py| ---------> | summarize.py | --------------> | |
+-----------+ | (uses llm.py) | | |
+--------------------+ | storage.py |
pipeline.py orchestrates fetch -> summarize -> store --> | (SQLite) |
| |
+-----------+
^
|
api.py (FastAPI)
GET /stories, /health
POST /pipeline/run


Every external dependency (`HackerNewsClient`, `StorySummarizer`, `OpenRouterClient`,
`StoryRepository`) is injected rather than hard-coded, which is what makes the
whole pipeline testable end-to-end without any network calls or a real API key.

## Tech stack

- **Python 3.12**
- **OpenRouter** (via the OpenAI-compatible SDK) for LLM summarization/categorization —
  model is swappable via a single environment variable, no code changes needed
- **FastAPI** + **Uvicorn** for the web service
- **SQLite** (stdlib `sqlite3`) for storage
- **pytest** for testing (all external calls mocked — no network or API key needed to run the suite)
- **python-dotenv** for local config

## Project structure

techpulse/
├── techpulse/
│ ├── fetcher.py # Hacker News API client
│ ├── llm.py # OpenRouter client (model swappable via env var, retry/backoff)
│ ├── summarize.py # Prompting + defensive JSON parsing on top of llm.py
│ ├── storage.py # SQLite persistence layer
│ ├── pipeline.py # Orchestrates fetch -> summarize -> store
│ └── api.py # FastAPI service
├── tests/ # Fully mocked, no network/API key needed
├── .env.example
└── requirements.txt


## Setup

```bash
git clone <your-repo-url>
cd techpulse
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and add your OPENROUTER_API_KEY and OPENROUTER_MODEL
```

Get a free OpenRouter API key at [openrouter.ai/keys](https://openrouter.ai/keys) — no
credit card required. Several models are available at no cost under `:free` model IDs.

## Usage

### Run the pipeline directly

```bash
python3 -c "
from techpulse.pipeline import run_pipeline
processed = run_pipeline(limit=10, db_path='techpulse.db')
print(f'Processed {processed} stories')
"
```

### Run the API

```bash
uvicorn techpulse.api:app --reload
```

Visit `http://localhost:8000/docs` for interactive Swagger docs, or:

```bash
# Trigger a pipeline run (fetches, summarizes, stores)
curl -X POST "http://localhost:8000/pipeline/run?limit=10"

# List stories, optionally filtered
curl "http://localhost:8000/stories?category=AI/ML&min_score=50"

# Get a single story
curl "http://localhost:8000/stories/12345"
```

## Running the tests

```bash
pytest -v
```

All tests run fully offline — no OpenRouter API key or network access is required,
since every external dependency is mocked or fake-injected via dependency injection.

## Design decisions worth calling out

- **Dependency injection everywhere.** `run_pipeline()`, `StorySummarizer`, and the
  FastAPI `get_repository` dependency all accept their collaborators as
  constructor/function arguments, which is what makes the whole pipeline testable
  without hitting a real API or database.
- **Model is a config value, not a code value.** `OPENROUTER_MODEL` in `.env` controls
  which model `llm.py` calls — swapping models is a one-line config change, not a
  refactor.
- **Retry with exponential backoff.** `llm.py` retries transient failures (rate limits,
  empty responses, malformed provider output) up to 3 times with increasing delays,
  since these are common and expected when using shared free-tier model pools.
- **Defensive LLM output parsing.** `summarize.py` asks the model for strict JSON, then
  parses it defensively (handling markdown code fences, malformed JSON, and invalid
  categories) rather than assuming a clean response — a common real-world failure mode
  when working with LLM output.
- **Upsert instead of insert.** `storage.py` uses `INSERT ... ON CONFLICT DO UPDATE`
  so re-running the pipeline against the same stories updates scores/summaries instead
  of creating duplicates.
- **One bad story shouldn't kill the run.** `pipeline.py` catches per-story exceptions
  and continues, logging failures rather than crashing the whole batch.

## Known limitations / caveats

- **Free-tier model reliability.** This project intentionally uses free models on
  OpenRouter to keep the project's operating cost at $0. In practice, free models
  are served from shared capacity pools and can return transient errors — including
  `429` (rate limited) and occasionally `502` (upstream provider failure) — especially
  under load. The retry/backoff logic in `llm.py` absorbs most of these automatically,
  but a `502` from the upstream provider itself is outside this app's control. If you
  hit persistent `502`s, the fix is simply to swap `OPENROUTER_MODEL` in `.env` to a
  different `:free` model — no code changes required.
- SQLite is used for simplicity and zero setup; a production deployment with concurrent
  writers would want Postgres instead (see Next steps).

## Possible next steps

- Add a CLI entrypoint and containerize with Docker
- Add CI (lint + test on every push)
- Swap SQLite for Postgres for concurrent/production use
- Add scheduled runs (cron / GitHub Actions scheduled workflow)
- Cache LLM responses by story ID to avoid re-summarizing on re-runs

## License

MIT
