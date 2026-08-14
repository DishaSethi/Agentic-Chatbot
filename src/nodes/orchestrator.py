from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.types import Send
from config.settings import llm
from src.schemas.state import State
from src.schemas.models import ArchitecturePlan
from src.prompts.system_prompts import ORCH_SYSTEM

def orchestrator_node(state: State) -> dict:
    print(f"\n🧠 [Architect] Designing the system architecture plan...")
    planner = llm.with_structured_output(ArchitecturePlan)
    plan = planner.invoke([
        SystemMessage(content=ORCH_SYSTEM),
        HumanMessage(content=f"System Requirement: {state['topic']}\nMode: {state.get('mode')}\nEvidence: {[e.model_dump() for e in state.get('evidence', [])][:10]}"),
    ])
    return {"plan": plan}

def fanout(state: State):
    assert state["plan"] is not None
    return [
        Send("worker", {
            "task": task.model_dump(),
            "topic": state["topic"],
            "mode": state["mode"],
            "plan": state["plan"].model_dump(),
            "evidence": [e.model_dump() for e in state.get("evidence", [])],
        })
        for task in state["plan"].tasks
    ]