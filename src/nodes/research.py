from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import llm
from src.schemas.state import State
from src.schemas.models import EvidencePack
from src.prompts.system_prompts import RESEARCH_SYSTEM
from src.tools.search import tavily_search

def research_node(state: State) -> dict:
    print(f"\n🔍 [Researcher] Searching the web for the latest documentation...")
    queries = (state.get("queries") or [])[:5]
    raw = []
    for q in queries:
        raw.extend(tavily_search(q, max_results=3))

    if not raw:
        return {"evidence": []}

    extractor = llm.with_structured_output(EvidencePack)
    pack = extractor.invoke([
        SystemMessage(content=RESEARCH_SYSTEM),
        HumanMessage(content=f"Raw Search Results:\n{raw}"),
    ])

    dedup = {e.url: e for e in pack.evidence if e.url}
    return {"evidence": list(dedup.values())}