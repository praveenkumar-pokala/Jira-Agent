import os, csv, io, json
from typing import List, Dict
import httpx
from pydantic import BaseModel
from schema import Feature, Story, AcceptanceCriterion, TestCase, TestStep

def get_env() -> Dict[str, str]:
    return {
        "JIRA_BASE_URL": os.getenv("JIRA_BASE_URL", ""),
        "JIRA_EMAIL": os.getenv("JIRA_EMAIL", ""),
        "JIRA_API_TOKEN": os.getenv("JIRA_API_TOKEN", ""),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", ""),
        "PORT": os.getenv("PORT", "8000"),
    }

class JiraClient:
    def __init__(self, base_url: str, email: str, api_token: str):
        self.base_url = base_url.rstrip("/")
        self.auth = (email, api_token)
        self.headers = {"Accept":"application/json"}

    async def fetch_epics_by_jql(self, jql: str) -> List[Feature]:
        url = f"{self.base_url}/rest/api/3/search"
        params = {"jql": jql, "fields": "summary,description,issuetype"}
        async with httpx.AsyncClient() as client:
            r = await client.get(url, params=params, headers=self.headers, auth=self.auth, timeout=30)
            r.raise_for_status()
            data = r.json()
        feats: List[Feature] = []
        for issue in data.get("issues", []):
            fields = issue.get("fields", {})
            itype = (fields.get("issuetype", {}) or {}).get("name","").lower()
            if itype != "epic":
                continue
            feats.append(Feature(
                id=issue.get("id"),
                key=issue.get("key"),
                title=fields.get("summary") or f"Epic {issue.get('key')}",
                description=fields.get("description") if isinstance(fields.get("description"), str) else ""
            ))
        return feats

class AIStatus(BaseModel):
    available: bool = False
    last_error: str = ""

class AIClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.status = AIStatus(available=bool(api_key))

    def _template_story(self, feature: Feature, idx: int) -> Story:
        return Story(
            story_id=f"ST-{idx+1:03d}",
            title=f"{feature.title} — User Story {idx+1}",
            as_a="end user",
            i_want=f"capability related to {feature.title.lower()}",
            so_that="I achieve my goal",
            story_points=3,
            acceptance=[
                AcceptanceCriterion(text=f"Accept when flow for '{feature.title}' works"),
                AcceptanceCriterion(text="Reject invalid inputs with helpful messages")
            ],
        )

    def _template_tests(self, story: Story, i: int) -> TestCase:
        return TestCase(
            case_id=f"TC-{i+1:03d}",
            story_id=story.story_id,
            preconditions="User authenticated",
            steps=[
                TestStep(step="Open app", expected="Dashboard loads"),
                TestStep(step=f"Go to {story.title}", expected="Screen visible"),
                TestStep(step="Perform primary action", expected="Success state")
            ]
        )

    def generate_stories(self, features: List[Feature], strategy: str) -> List[Story]:
        use_ai = self.status.available and strategy != "template_only"
        stories: List[Story] = []
        for i, f in enumerate(features):
            stories.append(self._template_story(f, i))
        return stories

    def generate_tests(self, stories: List[Story]) -> List[TestCase]:
        tests: List[TestCase] = []
        for i, s in enumerate(stories):
            tests.append(self._template_tests(s, i))
        return tests

def export_json(stories: List[Story], tests: List[TestCase]) -> str:
    return json.dumps({
        "stories":[s.model_dump() for s in stories],
        "tests":[t.model_dump() for t in tests],
    }, indent=2)

def export_csv(stories: List[Story], tests: List[TestCase]) -> str:
    buf = io.StringIO()
    sw = csv.writer(buf)
    sw.writerow(["Stories"])
    sw.writerow(["story_id","title","as_a","i_want","so_that","story_points","acceptance"])
    for s in stories:
        sw.writerow([
            s.story_id, s.title, s.as_a, s.i_want, s.so_that, s.story_points,
            " | ".join(a.text for a in s.acceptance)
        ])
    sw.writerow([])
    sw.writerow(["TestCases"])
    sw.writerow(["case_id","story_id","preconditions","steps"])
    for t in tests:
        steps_txt = " | ".join(f"{st.step} => {st.expected}" for st in t.steps)
        sw.writerow([t.case_id, t.story_id, t.preconditions or "", steps_txt])
    return buf.getvalue()

def export_md(stories: List[Story], tests: List[TestCase]) -> str:
    lines = ["# Jira AI Agent — Export", ""]
    lines.append("## Stories")
    for s in stories:
        lines += [
            f"### {s.story_id} — {s.title}",
            f"- As a **{s.as_a}** I want **{s.i_want}** so that **{s.so_that}**.",
            f"- Story points: **{s.story_points}**",
            f"- Acceptance:",
        ]
        for a in s.acceptance:
            lines.append(f"  - {a.text}")
        lines.append("")
    lines.append("## Test Cases")
    for t in tests:
        lines += [
            f"### {t.case_id} — for {t.story_id}",
            f"- Preconditions: {t.preconditions or '-'}",
            f"- Steps:",
        ]
        for st in t.steps:
            lines.append(f"  1. {st.step} → _{st.expected}_")
        lines.append("")
    return "\n".join(lines)
