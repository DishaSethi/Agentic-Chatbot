from pydantic import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import llm
from src.schemas.state import State

class GradeDocument(BaseModel):
    binary_score: str = Field(description="Relevance score 'yes' or 'no'")

GRADER_SYSTEM = """You are a technical document grader.
Assess if the retrieved document is highly relevant to the requested system architecture.
If it is irrelevant marketing fluff or completely off-topic, grade it 'no'.
Otherwise, grade it 'yes'.
"""

def grader_node(state: State) -> dict:
    print(f"\n⚖️ [Grader] Evaluating retrieved search results...", flush=True)
    grader = llm.with_structured_output(GradeDocument)
    relevant_evidence = []

    for item in state.get("evidence", []):
        score = grader.invoke([
            SystemMessage(content=GRADER_SYSTEM),
            HumanMessage(content=f"Topic: {state['topic']}\nDocument Snippet: {item.snippet}")
        ])

        if score.binary_score.lower() == "yes":
            relevant_evidence.append(item)
        else:
            print(f"   ❌ [Grader] Discarded irrelevant source: {item.url}", flush=True)

    print(f"   ✅ [Grader] Kept {len(relevant_evidence)} high-quality sources.", flush=True)

    # CRAG LOGIC: If we don't have enough good evidence, we need to rewrite and try again!
    current_loops = state.get("research_loop_count", 0)

    # If we have less than 2 good sources AND we haven't looped too many times (max 2)
    needs_rewrite = len(relevant_evidence) < 2 and current_loops < 2

    if needs_rewrite:
        print(f"   ⚠️ [Grader] Not enough quality evidence. Triggering Query Rewrite...", flush=True)

    return {
        "evidence": relevant_evidence,
        # We temporarily hijack "needs_research" to route our conditional logic in the graph
        "needs_research": needs_rewrite
    }