from langgraph.graph import StateGraph, START, END
from src.schemas.state import State
from src.nodes.router import router_node, route_next
from src.nodes.research import research_node
from src.nodes.grader import grader_node
from src.nodes.rewriter import rewriter_node
from src.nodes.orchestrator import orchestrator_node, fanout
from src.nodes.worker import worker_node
from src.graph.reducer_graph import reducer_subgraph
from langgraph.checkpoint.memory import MemorySaver

g = StateGraph(State)
g.add_node("router", router_node)
g.add_node("research", research_node)
g.add_node("grader", grader_node)
g.add_node("rewriter", rewriter_node)
g.add_node("orchestrator", orchestrator_node)
g.add_node("worker", worker_node)
g.add_node("reducer", reducer_subgraph)

g.add_edge(START, "router")
g.add_conditional_edges("router", route_next, {"research": "research", "orchestrator": "orchestrator"})
g.add_edge("research", "grader")

def evaluate_crag(state:State)-> str:
    if state.get("needs_research"):
        return "rewrite"
    return "continue"

g.add_conditional_edges(
    "grader",
    evaluate_crag,
    {"rewrite":"rewriter","continue":"orchestrator"}
)
g.add_edge("rewriter", "research")
# g.add_edge("research", "orchestrator")
g.add_conditional_edges("orchestrator", fanout, ["worker"])
g.add_edge("worker", "reducer")
g.add_edge("reducer", END)

memory=MemorySaver()

app = g.compile(
    checkpointer=memory,
    interrupt_before=["worker"]
)