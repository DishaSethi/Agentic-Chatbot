from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class EngineeringTask(BaseModel):
    id: int
    title: str
    goal: str = Field(..., description="Technical component being documented.")
    bullets: List[str] = Field(..., min_length=3, max_length=6)
    target_words: int = Field(..., description="Target word count (150-400).")
    requires_code: bool = Field(default=True, description="Needs code blocks, JSON schemas, or YAML configs.")


class ArchitecturePlan(BaseModel):
    system_title: str
    target_audience: str = "Engineering Leadership & Development Team"
    doc_kind: Literal["technical_design_document", "rfc", "arc42"] = "technical_design_document"
    tasks: List[EngineeringTask]

class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None

class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    reason: str
    queries: List[str] = Field(default_factory=list)
    max_results_per_query: int = Field(3)

class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)

class ImageSpec(BaseModel):
    placeholder: str = Field(..., description="e.g. [[IMAGE_1]]")
    filename: str = Field(..., description="Save under images/, e.g. system_architecture.png")
    alt: str
    caption: str
    prompt: str = Field(..., description="Prompt for Gemini to draw a clean technical architecture diagram.")

class GlobalImagePlan(BaseModel):
    md_with_placeholders: str
    images: List[ImageSpec] = Field(default_factory=list)


class EvaluateRequest(BaseModel):
    user_architecture:str

class PlanRequest(BaseModel):
    topic:str

class ApproveRequest(BaseModel):
    thread_id:str
    topic:str