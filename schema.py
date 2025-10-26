from typing import List, Optional
from pydantic import BaseModel, Field

class Feature(BaseModel):
    id: Optional[str] = Field(None, description="Local or Jira id")
    key: Optional[str] = Field(None, description="Jira issue key")
    title: str = Field(..., description="Feature/Epic title")
    description: Optional[str] = Field(None, description="Details")

class AcceptanceCriterion(BaseModel):
    text: str

class Story(BaseModel):
    story_id: str
    title: str
    as_a: str
    i_want: str
    so_that: str
    story_points: int = 3
    acceptance: List[AcceptanceCriterion] = []

class TestStep(BaseModel):
    step: str
    expected: str

class TestCase(BaseModel):
    case_id: str
    story_id: str
    preconditions: Optional[str] = None
    steps: List[TestStep] = []

class IngestJiraRequest(BaseModel):
    jql: str

class IngestMockRequest(BaseModel):
    __root__: List[Feature]

class GenerateRequest(BaseModel):
    strategy: str = "ai_or_template"
