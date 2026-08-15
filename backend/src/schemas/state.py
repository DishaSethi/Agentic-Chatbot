import operator
from typing import TypedDict, List, Optional, Annotated
from src.schemas.models import EvidenceItem, ArchitecturePlan

class State(TypedDict):
    topic: str
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[ArchitecturePlan]
    as_of: str
    recency_days: int
    sections: Annotated[List[tuple[int, str]], operator.add]
    merged_md: str
    md_with_placeholders: str
    image_specs: List[dict]
    final: str
    research_loop_count:int