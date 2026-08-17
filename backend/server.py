import os
import uuid
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv       # <--- IMPORT DOTENV
import psycopg2                      # <--- IMPORT POSTGRES DRIVER
from psycopg2.extras import RealDictCursor # <--- Returns DB rows as Python dictionaries
from pgvector.psycopg2 import register_vector
from src.graph.main_graph import app as graph_engine
from google import genai
from google.genai import types
from typing import TypedDict
from langgraph.graph import StateGraph, END


# --- DATABASE CONFIGURATION ---
# Load variables from the .env file
load_dotenv()
gemini_client=genai.Client()



# Get the Neon DB URL from the environment
DATABASE_URL = os.getenv("DB_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the .env file!")

app = FastAPI(title="AI Architect API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluateRequest(BaseModel):
    user_architecture: str

class PlanRequest(BaseModel):
    topic: str

class ApproveRequest(BaseModel):
    thread_id: str
    topic: str

@app.post("/api/plan")
async def generate_plan(req: PlanRequest):
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    initial_state = {
        "topic": req.topic,
        "as_of": date.today().isoformat(),
        "research_loop_count": 0
    }

    for chunk in graph_engine.stream(initial_state, config=config):
        pass

    current_state = graph_engine.get_state(config)
    plan = current_state.values.get("plan")

    if not plan:
        raise HTTPException(status_code=500, detail="Planning failed.")

    return {
        "thread_id": thread_id,
        "system_title": plan.system_title,
        "tasks": [{"title": t.title, "goal": t.goal, "bullets": t.bullets} for t in plan.tasks]
    }

@app.post("/api/generate")
async def generate_document(req: ApproveRequest):
    config = {"configurable": {"thread_id": req.thread_id}}

    for chunk in graph_engine.stream(None, config=config):
        pass

    final_state = graph_engine.get_state(config)
    final_md = final_state.values.get("merged_md")


    doc_id = None
    try:
        # Open connection to Neon
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Execute the INSERT query and RETURNING id gets the auto-generated UUID back
        cursor.execute(
            "INSERT INTO architectures (topic, markdown) VALUES (%s, %s) RETURNING id;",
            (req.topic, final_md)
        )

        # Fetch the newly created ID
        inserted_row = cursor.fetchone()
        if inserted_row:
            doc_id = inserted_row["id"]

        # Commit the transaction and close the connection
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        print(f"Neon Database error: {e}")

    return {
        "markdown": final_md,
        "doc_id": doc_id
    }

@app.get("/api/document/{doc_id}")
async def get_document(doc_id: str):
    try:
        # Open connection to Neon
        conn = psycopg2.connect(DATABASE_URL)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Fetch the document by ID
        cursor.execute("SELECT * FROM architectures WHERE id = %s;", (doc_id,))
        document = cursor.fetchone()

        cursor.close()
        conn.close()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        return document

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# 🧠 SELF-RAG LANGGRAPH SETUP
# ==========================================
class EvaluateState(TypedDict):
    user_architecture: str
    context: str
    draft_scorecard: str
    is_hallucinated: bool
    iterations: int

def generate_scorecard(state: EvaluateState):
    print(f"🔄 [LangGraph] Generator Node (Attempt {state['iterations'] + 1})...")

    system_prompt = f"""You are a Principal Cloud Systems Architect.
Evaluate the user's architecture against these rules:
{state['context']}

CRITICAL INSTRUCTION FOR CITATIONS:
Whenever you enforce a constraint or apply a rule from the provided context, you MUST cite it inline using the category name in brackets.
Example: "You must use a message broker [Scalability]."
Do not invent rules or cite things not in the context.

Generate a comprehensive Markdown evaluation report structured as follows:
## 📊 Architecture Evaluation Scorecard
### 1. Strengths & Good Alignment
### 2. Critical Bottlenecks & Security Gaps
### 3. Recommendations & Mitigations
"""
    # If the grader rejected the last draft, add a stern warning!
    if state['iterations'] > 0:
        system_prompt += "\n\nWARNING: Your previous draft hallucinated rules. STICK STRICTLY TO THE PROVIDED CONTEXT AND DO NOT INVENT BEST PRACTICES."


    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f"{system_prompt}\n\nUser Architecture:\n{state['user_architecture']}"
    )
    return {"draft_scorecard": response.text, "iterations": state['iterations'] + 1}

def grade_hallucinations(state: EvaluateState):
    print("🕵️ [LangGraph] Grader Node checking for hallucinations...")

    grader_prompt = f"""You are a strict Hallucination Grader.
DATABASE RULES:
{state['context']}

DRAFT REPORT:
{state['draft_scorecard']}

Did the draft report invent any rules, constraints, or technologies that are NOT mentioned in the DATABASE RULES?
Respond with ONLY 'YES' (it hallucinated) or 'NO' (it is clean).
"""

    response = gemini_client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=grader_prompt
    )

    answer = response.text.strip().upper()
    is_hallucinated = "YES" in answer

    if is_hallucinated:
        print("🚨 HALLUCINATION DETECTED! Rejecting draft and looping back...")
    else:
        print("✅ DRAFT APPROVED! Clean architecture evaluation ready.")

    return {"is_hallucinated": is_hallucinated}


@app.post("/api/evaluate")
async def evaluate_architecture(req: EvaluateRequest):
    try:
        embed_response = gemini_client.models.embed_content(
            model="gemini-embedding-001",
            contents=req.user_architecture,
        )
        query_embedding = embed_response.embeddings[0].values

        conn = psycopg2.connect(DATABASE_URL)
        register_vector(conn)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("""WITH vector_search AS (
        SELECT category, content, source_url, RANK() OVER(ORDER BY embedding <=> %s:: vector) AS dense_rank FROM best_practices LIMIT 10),
        keyword_search AS (
        SELECT category, content, source_url , RANK() OVER(ORDER BY ts_rank_cd(
        to_tsvector('english', content), websearch_to_tsquery('english',%s))DESC) AS sparse_rank
        FROM best_practices
        WHERE to_tsvector('english', content) @@ websearch_to_tsquery('english',%s) LIMIT 10)
        SELECT
        COALESCE(v.category, k.category) AS category,
        COALESCE(v.content, k.content) AS content,
        COALESCE(v.source_url, k.source_url) AS source_url,
        --RRF Formula:1/(RANK+k) where k is usually 60
        (COALESCE(1.0/(v.dense_rank+60),0.0)+COALESCE(1.0/(k.sparse_rank+60),0.0)) AS rrf_score
        FROM vector_search v
        FULL OUTER JOIN keyword_search k ON v.content=k.content
        ORDER BY rrf_score DESC
        LIMIT 3;  """,(
            query_embedding,
            req.user_architecture,
            req.user_architecture
        ))

        retrieved_docs = cursor.fetchall()
        cursor.close()
        conn.close()

        # ==========================================
        # 🕵️ AUDIT 1: WHAT DID NEON DB FIND?
        # ==========================================
        print("\n" + "="*50)
        print("🔍 RAG AUDIT: TOP 3 MATCHES FROM NEON DB")
        print("="*50)
        if not retrieved_docs:
            print("⚠️ WARNING: DB returned ZERO results.")
        for i, doc in enumerate(retrieved_docs):
            score=f"{doc.get('rrf_score',0):.4f}"
            print(f"\n--- MATCH {i+1} [{doc['category']}] (Score:{score}) ---")
            print(f"CONTENT: {doc['content'][:150]}")
        print("="*50 + "\n")

        # 3. Build context and citations payload
        citations_payload = []
        if retrieved_docs:
            context = ""
            for doc in retrieved_docs:
                category_id = doc['category']
                context += f"[{category_id}] {doc['content']}\n\n"

                # Build the metadata object for the React frontend
                citations_payload.append({
                    "id": category_id,
                    "title": category_id,
                    "content": doc['content'],
                    "url":doc.get('source_url','#')
                })
        else:
            context = "General Distributed Systems and Cloud Architecture Best Practices."

        # ==========================================
        # ⚙️ EXECUTE LANGGRAPH SELF-RAG LOOP
        # ==========================================
        # Notice this is OUTSIDE the 'else' block! It runs every time.
        workflow = StateGraph(EvaluateState)

        workflow.add_node("generator", generate_scorecard)
        workflow.add_node("grader", grade_hallucinations)

        workflow.set_entry_point("generator")
        workflow.add_edge("generator", "grader")

        def router(state: EvaluateState):
            if state["is_hallucinated"] and state["iterations"] < 3:
                return "generator"
            return END

        workflow.add_conditional_edges("grader", router)
        app_graph = workflow.compile()

        print("\n" + "="*50)
        print("🚀 STARTING LANGGRAPH SELF-RAG LOOP")
        print("="*50)

        final_state = app_graph.invoke({
            "user_architecture": req.user_architecture,
            "context": context,
            "draft_scorecard": "",
            "is_hallucinated": False,
            "iterations": 0
        })

        # Return the final output to React
        return {
            "evaluation_scorecard": final_state["draft_scorecard"],
            "matched_rules_count": len(retrieved_docs),
            "citations": citations_payload
        }

    except Exception as e:
        print(f"RAG Evaluation Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    """Fetches the list of past architecture designs"""
    try:
        conn=psycopg2.connect(DATABASE_URL)
        cursor=conn.cursor(cursor_factory=RealDictCursor)

        # Fetch the latest 15 designs (only grabbing the ID and topic to save bandwidth)
        cursor.execute("SELECT id, topic FROM architectures ORDER BY id DESC LIMIT 15;")
        records=cursor.fetchall()

        cursor.close()
        conn.close()
        return records
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{doc_id}")
async def get_history_document(doc_id:str):
    """Fetches the full markdown for a specific architecture"""
    try:
        conn=psycopg2.connect(DATABASE_URL)
        cursor=conn.cursor(cursor_factory=RealDictCursor)

        cursor.execute("SELECT topic, markdown FROM architectures WHERE id=%s;",(doc_id,))
        record=cursor.fetchone()

        cursor.close()
        conn.close()

        if not record:
            raise HTTPException(status_code=404, detail="Document not found")
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting FastAPI Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)