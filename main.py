from datetime import date
from src.schemas.state import State
from src.graph.main_graph import app

if __name__ == "__main__":
    initial_state: State = {
        "topic": "Design a real-time multiplayer Chess backend using WebSockets, Node.js, and Redis Pub/Sub.",
        "as_of": date.today().isoformat(),
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "recency_days": 365,
        "sections": [],
        "merged_md": "",
        "md_with_placeholders": "",
        "image_specs": [],
        "final": "",
        "research_loop_count":0
    }

    print("\n=======================================================")
    print("🚀 STARTING AI SYSTEM ARCHITECT ENGINE")
    print("=======================================================")

    # We replace app.invoke() with app.stream() to watch the graph move node-by-node
    for chunk in app.stream(initial_state, stream_mode="updates"):
        for node_name, state_update in chunk.items():
            print(f"✅ [LangGraph] Finished executing node: {node_name.upper()}")

    print("\n=======================================================")
    print("🎉 SYSTEM DOCUMENTATION GENERATED SUCCESSFULLY!")
    print("=======================================================")