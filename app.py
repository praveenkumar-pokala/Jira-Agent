from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from dotenv import load_dotenv

from schema import Feature, IngestJiraRequest, IngestMockRequest, GenerateRequest, Story, TestCase
from utils import get_env, JiraClient, AIClient, export_json, export_csv, export_md

load_dotenv()
app = FastAPI(title="Jira AI Agent — Commented Demo")

MEM = {"features": [], "stories": [], "tests": []}
ENV = get_env()
jira = JiraClient(ENV["JIRA_BASE_URL"], ENV["JIRA_EMAIL"], ENV["JIRA_API_TOKEN"])
ai = AIClient(ENV["GEMINI_API_KEY"])

@app.get("/", response_class=PlainTextResponse)
async def health():
    return "ok"

@app.get("/__env_check")
async def env_check():
    return {k: ("set" if v else "unset") for k, v in ENV.items()}

@app.get("/__ai_engine")
async def ai_engine_status():
    return ai.status.model_dump()

@app.get("/__ai_status")
async def ai_status() -> bool:
    return ai.status.available

@app.post("/ingest/jira")
async def ingest_jira(req: IngestJiraRequest):
    if not (ENV["JIRA_BASE_URL"] and ENV["JIRA_EMAIL"] and ENV["JIRA_API_TOKEN"]):
        raise HTTPException(status_code=400, detail="Jira env not configured")
    feats = await jira.fetch_epics_by_jql(req.jql)
    MEM["features"] = feats
    return {"count": len(feats), "message": "loaded features from Jira"}

@app.post("/ingest/mock")
async def ingest_mock(req: IngestMockRequest):
    feats: List[Feature] = [Feature(**f) if isinstance(f, dict) else f for f in req.__root__]
    MEM["features"] = feats
    return {"count": len(feats), "message": "loaded mock features"}

@app.post("/generate/stories")
async def generate_stories(req: GenerateRequest):
    if not MEM["features"]:
        raise HTTPException(status_code=400, detail="No features loaded; ingest first")
    stories = ai.generate_stories(MEM["features"], req.strategy)
    MEM["stories"] = stories
    return {"count": len(stories)}

@app.post("/generate/tests")
async def generate_tests():
    if not MEM["stories"]:
        raise HTTPException(status_code=400, detail="No stories available; generate stories first")
    tests = ai.generate_tests(MEM["stories"])
    MEM["tests"] = tests
    return {"count": len(tests)}

@app.get("/export", response_class=PlainTextResponse)
async def export(fmt: str = "json"):
    if fmt == "json":
        return export_json(MEM["stories"], MEM["tests"])
    if fmt == "csv":
        return export_csv(MEM["stories"], MEM["tests"])
    if fmt == "md":
        return export_md(MEM["stories"], MEM["tests"])
    raise HTTPException(status_code=400, detail="fmt must be one of: json,csv,md")
