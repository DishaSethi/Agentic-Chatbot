from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import llm
from src.schemas.state import State
from src.schemas.models import RouterDecision
from src.prompts.system_prompts import ROUTER_SYSTEM

def router_node(state: State) -> dict:
    print(f"\n🚦 [Router] Analyzing requirements to determine if web research is needed...")
    decider = llm.with_structured_output(RouterDecision)
    decision = decider.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=f"System Specification Prompt: {state['topic']}\nAs-of date: {state['as_of']}"),
    ])

    recency_days = 30 if decision.mode == "open_book" else (180 if decision.mode == "hybrid" else 3650)
    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
        "recency_days": recency_days,
    }

def route_next(state: State) -> str:
    return "research" if state["needs_research"] else "orchestrator"