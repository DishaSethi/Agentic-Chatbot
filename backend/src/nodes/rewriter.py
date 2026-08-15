from pydantic import BaseModel, Field
from typing import List
from langchain_core.messages import SystemMessage, HumanMessage
from config.settings import llm
from src.schemas.state import State

class RewrittenQueries(BaseModel):
    queries:List[str]=Field(description="List of 3 highly technical, highly specific search queries")

REWRITER_SYSTEM = """You are an expert technical researcher.
The previous web searches failed to find highly relevant technical documentation for the system architecture.
Analyze the original system prompt and the failed queries, then generate 3 NEW, highly specific search queries.
Include specific technology names, versions, and keywords like 'architecture', 'system design', or 'GitHub'.
"""

def rewriter_node(state:State)-> dict:
    print(f"\n[Rewriter ] Optimizing search queries for search better results....",flush =True)

    rewriter_chain=llm.with_structured_output(RewrittenQueries)

    rewriter=rewriter_chain.invoke([
        SystemMessage(content=REWRITER_SYSTEM),
        HumanMessage(content=f"System Prompt:{state ['topic']}\nOld Failed Queries:{state.get('queries')}")
    ])

    new_loop_count=state.get("research_loop_count",0)+1

    print(f"[Rewriter] New Queries:{rewriter.queries}",flush=True)

    return{
        "queries":rewriter.queries,
        "research_loop_count":new_loop_count
    }


