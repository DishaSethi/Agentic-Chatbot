from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
from config.settings import llm
from src.schemas.models import EngineeringTask, ArchitecturePlan, EvidenceItem
from src.prompts.system_prompts import WORKER_SYSTEM

def worker_node(payload: dict) -> dict:
    task = EngineeringTask(**payload["task"])
    plan = ArchitecturePlan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]

    print(f"   👷 [Engineer] Drafting section: {task.title}...")

    # We pipe the LLM output directly into StrOutputParser() to guarantee a string
    chain = llm | StrOutputParser()

    section_md = chain.invoke([
        SystemMessage(content=WORKER_SYSTEM),
        HumanMessage(content=f"System Title: {plan.system_title}\nSection: {task.title}\nGoal: {task.goal}\nBullets: {task.bullets}\nEvidence: {[e.url for e in evidence]}"),
    ]).strip()

    return {"sections": [(task.id, section_md)]}