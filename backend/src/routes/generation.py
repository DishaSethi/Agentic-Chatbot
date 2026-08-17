import uuid
from datetime import date
from fastapi import APIRouter, HTTPException
from psycopg2.extras import RealDictCursor

from src.schemas.models import PlanRequest, ApproveRequest
from src.db import get_db_connection
from src.graph.main_graph import app as graph_engine

router = APIRouter()

@router.post("/api/plan")
async def generate_plan(req: PlanRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {"topic": req.topic, "as_of": date.today().isoformat(), "research_loop_count": 0}

    for chunk in graph_engine.stream(initial_state, config=config): pass

    current_state = graph_engine.get_state(config)
    plan = current_state.values.get("plan")
    if not plan: raise HTTPException(status_code=500, detail="Planning failed.")

    return {
        "thread_id": thread_id, "system_title": plan.system_title,
        "tasks": [{"title": t.title, "goal": t.goal, "bullets": t.bullets} for t in plan.tasks]
    }

@router.post("/api/generate")
async def generate_document(req: ApproveRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    for chunk in graph_engine.stream(None, config=config): pass

    final_state = graph_engine.get_state(config)
    final_md = final_state.values.get("merged_md")

    doc_id = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("INSERT INTO architectures (topic, markdown) VALUES (%s, %s) RETURNING id;", (req.topic, final_md))
        inserted_row = cursor.fetchone()
        if inserted_row: doc_id = inserted_row["id"]
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Neon Database error: {e}")

    return {"markdown": final_md, "doc_id": doc_id}