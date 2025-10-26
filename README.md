# Jira AI Agent — Story & Test Case Generator 

This is a **fully commented** and slightly refactored scaffold of the original “Jira-AI-Agent-Demo” project. 
It implements an AI-powered workflow that turns Jira Epics (or mock feature JSON) into **user stories** 
(with acceptance criteria and story points) and **test cases** (preconditions, steps, expected results).

> Why this edition?  
> The goal is educational clarity. Every part of the backend has rich comments and docstrings so you can quickly understand how it works, extend it, or fork it for your org.

## Highlights

- **FastAPI backend** with clean, documented endpoints for:
  - ingesting Jira epics via JQL and mock feature JSON,
  - generating stories and test cases (with AI or template fallback),
  - exporting results to JSON/CSV/Markdown,
  - operational status checks.
- **Pluggable AI engine**: a simple interface wraps Gemini (or any LLM) and falls back to deterministic templates.
- **Typed schemas** via Pydantic for robust validation between layers.
- **Modern UI stub** (`index.html`) to show how a front-end can connect.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirement.txt
cp .env.example .env
uvicorn app:app --reload --port 8000
# open index.html in a browser or call APIs directly
```

## Configuration

Create a `.env` file in project root:

```
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=you@company.com
JIRA_API_TOKEN=
GEMINI_API_KEY=
PORT=8000
```

## API

- `GET /` health
- `GET /__env_check`
- `GET /__ai_engine`
- `GET /__ai_status`
- `POST /ingest/jira` (body: {"jql":"..."})
- `POST /ingest/mock` (body: [Feature,...])
- `POST /generate/stories` (body: {"strategy":"ai_or_template"|"template_only"})
- `POST /generate/tests`
- `GET /export?fmt=json|csv|md`

## Structure

```
.
├── app.py
├── schema.py
├── utils.py
├── index.html
├── mockdata.json
├── requirement.txt
├── .env.example
└── README.md
```

## Notes

- This scaffold is derived from the public description and endpoints. No code is copied verbatim.
- Replace the AI template with real Gemini calls if you have an API key.
